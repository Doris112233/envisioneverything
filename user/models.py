from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

class Patron(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures', null=True, blank=True)
    #borrow requests history (object list)

    def __str__(self):
        return f"Username: {self.user.username}"

    #save profile pic
    def save(self, *args, **kwargs): # Resizing image
        if self.pk:
            old_model = Patron.objects.filter(pk=self.pk).first()
            if old_model and self.profile_picture == old_model.profile_picture:
                super().save(*args, **kwargs)
                return
        if self.profile_picture:
            img = Image.open(self.profile_picture)
            img_format = img.format
            img.thumbnail((150, 150))
            # img = img.resize((400, 400))
            img_io = BytesIO()
            img.save(img_io, format=img_format)
            img_io.seek(0)
            new_filename = f"{self.profile_picture.name.split('/')[-1]}"
            self.profile_picture.save(new_filename, ContentFile(img_io.read()), save=False)
        super().save(*args, **kwargs)

    #delete profile pic (cannot refactor so just a note here)
    def delete(self, *args, **kwargs):
        if self.profile_picture:
            default_storage.delete(self.profile_picture.name)
        super().delete( *args, **kwargs)