from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.core.exceptions import ValidationError

def default_return_date():
    """Calculate the default return date as 7 days from now."""
    return now() + timedelta(days=7)

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_images', null=True, blank=True)
    description = models.TextField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100, default='Library')
    category = models.CharField(max_length=100, default='General')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_repairing = models.BooleanField(default=False)
    in_private_collection = models.BooleanField(default=False)
    #is_approved = models.BooleanField(default=False) #in the future, product will be approved by librarian
    #product history (object list)
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')


    def __str__(self):
        return f"Product name: {self.product_name} | Description: {self.description} | Price: {self.price} | Location: {self.location} | Category: {self.category} | Uploaded by: {self.uploaded_by.username if self.uploaded_by else 'N/A'}"

    def save(self, *args, **kwargs): # Resizing image
        if self.pk:
            old_product = Product.objects.filter(pk=self.pk).first()
            if old_product and self.image == old_product.image:
                super().save(*args, **kwargs)
                return
        if self.image:
            img = Image.open(self.image)
            img_format = img.format
            img.thumbnail((400, 400))
            # img = img.resize((400, 400))
            img_io = BytesIO()
            img.save(img_io, format=img_format)
            img_io.seek(0)
            new_filename = f"{self.image.name.split('/')[-1]}"
            self.image.save(new_filename, ContentFile(img_io.read()), save=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            default_storage.delete(self.image.name)
        super().delete( *args, **kwargs)

class Borrow(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'
        ON_RENT = 'On Rent', 'On Rent'
        RETURNED = 'Returned', 'Returned'
        # OVERDUE = 'Overdue', 'Overdue'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=now)
    return_date = models.DateTimeField(default=default_return_date) 
    # on_rent = models.BooleanField(default=False)
    # is_returned = models.BooleanField(default=False)
    is_overdue = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )


    def __str__(self):
        return f"User: {self.user.username} Product borrowed: {self.product.product_name} Date: {self.start_date} Status: {self.status} Is overdue: {self.is_overdue}"
    
    def new_borrow_request(self, user, product, start_date, return_date):
        """
        Creates a new borrow request if the product is available and the user has no overdue borrow requests.
        """
        if not product.is_available:
            raise ValueError("Product is not available for borrowing")

        # Check for overlapping borrow requests
        overlapping_borrows = Borrow.objects.filter(
            product=product,
            status__in=[Borrow.Status.APPROVED, Borrow.Status.ON_RENT],
            start_date__lt=return_date,
            return_date__gt=start_date
        )
        if overlapping_borrows.exists():
            raise ValueError("This product is already reserved for the selected dates.")

        overlapping_pending_borrows = Borrow.objects.filter(
            product=product,
            status=Borrow.Status.PENDING,
            start_date__lt=return_date,
            return_date__gt=start_date
        )
        if overlapping_pending_borrows.exists():
            raise ValueError("This product is already requested for the selected dates.")

        # Check for overdue borrows
        overdue_borrows = Borrow.objects.filter(user=user, is_overdue=True)
        if overdue_borrows.exists():
            raise ValueError("Please return your overdue item before borrowing")

        self.user = user
        self.product = product
        self.start_date = start_date
        self.return_date = return_date

        today = datetime.now().date()
        if start_date.date() < today or return_date.date() < today:
            raise ValueError("Start date and return date must not be in the past")
        if return_date.date() < start_date.date():
            raise ValueError("Return date must be after start date")
        if start_date.date() > (today + timedelta(days=365)) or return_date.date() > (today + timedelta(days=365)):
            raise ValueError("Start date and return date must not be more than a year in the future")

        self.save()
        product.is_available = False
        product.save()
    
    

class Collection(models.Model):
    collection_name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_collections')
    products = models.ManyToManyField(Product, related_name='collections')
    visibility_requests = models.ManyToManyField(User, related_name='requested_collections', blank=True)
    visible_to = models.ManyToManyField(User, related_name='visible_collections', blank=True)

    def __str__(self):
        return self.collection_name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.product_name}"
    

