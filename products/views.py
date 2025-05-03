from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .models import Product, Borrow, Collection, Review, Tag
from django.utils import timezone
from .forms import CollectionForm, ProductForm
from datetime import datetime
from django.db.models import Count
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib import messages

def get_context(request):
    has_pfp = False
    is_librarian = False
    patron = None
    if request.user.is_authenticated:
        is_librarian = request.user.groups.filter(name='librarian').exists()
        if hasattr(request.user, 'patron'):
            has_pfp = True
            patron = request.user.patron
    else:
        patron = None

    context = {
        'is_librarian': is_librarian,
        'has_pfp': has_pfp,
        'patron': patron
    }
    return context

def is_librarian(user):
    return user.is_authenticated and user.groups.filter(name='librarian').exists()

def browse_view(request):
    context = get_context(request)
    
    query = request.GET.get("q", "").strip() 
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(product_name__icontains=query) | 
            Q(tag__name__icontains=query)
        )

    context['products'] = products
    context['query'] = query 

    return render(request, "products/browse.html", context)

@login_required
def borrow_product_view(request, product_id):
    context = get_context(request) 
    product = get_object_or_404(Product, id = product_id)
    user = request.user
    has_borrow_request = Borrow.objects.filter(user=user, product=product, status__in=[Borrow.Status.PENDING, Borrow.Status.APPROVED]).exists()
    context['product'] = product
    context['borrow_request'] = has_borrow_request

    update_product_availability(product)

    # Get reviews for borrow display
    reviews = product.reviews.all()
    context['reviews'] = reviews

    if request.method == "POST":
        # Review submission
        if "rating" in request.POST and "comment" in request.POST:
            # Check if user has actually borrowed the product before allowing a review
            has_borrowed = Borrow.objects.filter(
                user=request.user,
                product=product,
                status=Borrow.Status.RETURNED
            ).exists()

            # If the user hasn't borrowed the product display error
            if not has_borrowed:
                context["review_error"] = "You must borrow and return this product before leaving a review."
                return render(request, "products/borrow_product.html", context)

            # Get the ratings on this product by this user 
            current_reviews = Review.objects.filter(
                user=request.user,
                product=product,
            )

            # Check if the user has already left two reviews
            # If they have already reviewed twice, display error
            if len(current_reviews) > 1:
                context["review_error"] = "You can only leave two reviews per product."
                return render(request, "products/borrow_product.html", context)

            # Otherwise create review
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')

            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )

            messages.success(request, "Review submitted successfully!")
            # Reload page after the review submission so user can see it 
            return redirect('borrow_product', product_id=product.id)

        # Borrow submission
        start_date = request.POST.get("start_date")
        return_date = request.POST.get("return_date")
        if not start_date or not return_date:
            context['error'] = "Please select both start and return dates."
            return render(request, "products/borrow_product.html", context)
        try:
            start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d")
            return_date = timezone.datetime.strptime(return_date, "%Y-%m-%d")
            borrow = Borrow()
            borrow.new_borrow_request(
                user=request.user,
                product=product,
                start_date=start_date,
                return_date=return_date,
            )
            context['success'] = "Product borrowed successfully!"
            return redirect("browse")

        except ValueError as e:
            context['error'] = str(e)
            return render(request, "products/borrow_product.html", context)
        
    if request.user.is_authenticated:
        if is_librarian(request.user):
            user_collections = Collection.objects.all()
        else:
            user_collections = Collection.objects.filter(creator=request.user)
        context['user_collections'] = user_collections

    return render(request, "products/borrow_product.html", context)


@login_required
@user_passes_test(is_librarian) #for the librarian to manage borrows
def manage_borrow_view(request):
    context = get_context(request)
    # borrows = Borrow.objects.all()
    update_borrow_statuses()
    today = timezone.now().date()
    pending_borrows = Borrow.objects.filter(status=Borrow.Status.PENDING)
    for borrow in pending_borrows:
        if borrow.start_date.date() < today:
            borrow.status = Borrow.Status.REJECTED
            borrow.save()
            messages.warning(
                request,
                f"Borrow request for {borrow.product.product_name} has been automatically rejected because the start date is in the past."
            )
    borrow_requests = Borrow.objects.filter(status__in=[Borrow.Status.PENDING, Borrow.Status.APPROVED])
    active_borrows = Borrow.objects.filter(status=Borrow.Status.ON_RENT)
    history_borrows = Borrow.objects.filter(status__in=[Borrow.Status.RETURNED, Borrow.Status.REJECTED])
    if request.method == "POST":
        borrow_id = request.POST.get("borrow_id")
        action = request.POST.get("action")
        if borrow_id and action:
            borrow = Borrow.objects.filter(id=borrow_id).first()
            if borrow:
                if action == "approve":
                    borrow.status = Borrow.Status.APPROVED
                    context["success"] = f"Borrow request for {borrow.product.product_name} approved."
                elif action == "reject":
                    borrow.status = Borrow.Status.REJECTED
                    context["success"] = f"Borrow request for {borrow.product.product_name} rejected."
                borrow.save()
                update_product_availability(borrow.product)
            else:
                context["error"] = "Invalid borrow request."

    # context["borrows"] = borrows
    context["borrow_requests"] = borrow_requests
    context["active_borrows"] = active_borrows
    context["history_borrows"] = history_borrows
    return render(request, "products/manage_borrow.html", context)

@login_required
def patron_manage_borrow_view(request):
    context = get_context(request)
    update_borrow_statuses()
    borrows = Borrow.objects.filter(user=request.user)
    borrow_requests = borrows.filter(status__in=[Borrow.Status.PENDING, Borrow.Status.APPROVED])
    active_borrows = borrows.filter(status=Borrow.Status.ON_RENT)
    history_borrows = borrows.filter(status__in=[Borrow.Status.RETURNED, Borrow.Status.REJECTED])

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        borrow = borrows.filter(product_id=product_id, status=Borrow.Status.ON_RENT).first()
        if borrow:
            # Update borrow status and related fields
            borrow.status = Borrow.Status.RETURNED
            borrow.is_overdue = False
            borrow.save()
            update_product_availability(borrow.product)
            messages.success(request, f"Successfully returned {borrow.product.product_name}!")
            # context["success"] = f"Successfully returned {borrow.product.product_name}!"
        else:
            messages.error(request, "You have not borrowed this product or it is not currently on rent.")
        return redirect("patron_manage_borrow")
        # return render(request, "products/patron_manage_borrow.html", context)
    context["borrow_requests"] = borrow_requests
    context["active_borrows"] = active_borrows
    context["history_borrows"] = history_borrows
    return render(request, "products/patron_manage_borrow.html", context)

def update_borrow_statuses():
    today = timezone.now().date()
    borrows = Borrow.objects.all()
    # Update approved borrows to on-rent when start date is today or earlier
    approved_borrows = borrows.filter(status=Borrow.Status.APPROVED)
    for borrow in approved_borrows:
        if borrow.start_date.date() <= today:
            borrow.status = Borrow.Status.ON_RENT
            borrow.save()
    
    # Update on-rent borrows to overdue when return date has passed
    on_rent_borrows = borrows.filter(status=Borrow.Status.ON_RENT)
    for borrow in on_rent_borrows:
        if borrow.return_date.date() < today:
            borrow.is_overdue = True
            borrow.save()
        else:
            borrow.is_overdue = False
            borrow.save()
    
    # Reset overdue flag for returned borrows
    returned_borrows = borrows.filter(status=Borrow.Status.RETURNED)
    for borrow in returned_borrows:
        if borrow.is_overdue:
            borrow.is_overdue = False
            borrow.save()
    
    # Update product availability based on current borrows
    products = Product.objects.all()
    for product in products:
        update_product_availability(product)

def update_product_availability(product):
    # Check if product is currently borrowed (on-rent)
    is_borrowed = Borrow.objects.filter(
        product=product, 
        status=Borrow.Status.ON_RENT
    ).exists()
    
    # Update product availability
    if not product.is_repairing:
        product.is_available = not is_borrowed
        product.save()

@login_required
@user_passes_test(is_librarian)
def manage_view(request):
    context = get_context(request)
    products = Product.objects.all()
    update_borrow_statuses()
    if request.method == "POST":
        action = request.POST.get("action")
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        if action == "send_to_repair":
            product.is_repairing = True
            product.is_available = False
            product.save()
            context["success"] = f"{product.product_name} has been sent for repair."
        elif action == "repair_complete":
            product.is_repairing = False
            product.is_available = True
            product.save()
            context["success"] = f"{product.product_name} has been marked as repaired and is now available."

    context['products'] = products
    return render(request, "products/manage.html", context)

@login_required
@user_passes_test(is_librarian)
def add_product_view(request):
    context = get_context(request)
    if request.POST:
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            product = product_form.save(commit=False)
            product.uploaded_by = request.user

            tag_name = product_form.cleaned_data.get('tag_name')
            if tag_name:
                tag_name = tag_name.lower().strip()
                tag, created = Tag.objects.get_or_create(name=tag_name)
                product.tag = tag
            
            product.save()
            return redirect("manage")
        else:
            print("Form errors:", product_form.errors)
    context['product_form'] = ProductForm()
    return render(request, 'products/add_product.html', context)

@login_required
@user_passes_test(is_librarian)
def edit_product_view(request, product_id):
    context = get_context(request)
    product = get_object_or_404(Product, id = product_id)

    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES, instance=product)
        if product_form.is_valid():
            if "image" not in request.FILES:
                product_form.instance.image = product.image

            tag_name = product_form.cleaned_data.get('tag_name')
            if tag_name:
                tag_name = tag_name.lower().strip()
                tag, created = Tag.objects.get_or_create(name=tag_name)
                product_form.instance.tag = tag
            else:
                product_form.instance.tag = None

            product_form.save()
            return redirect("manage")
        else:
            print("Form errors:", product_form.errors)
    else:
        product_form = ProductForm(instance=product)
    context['product_form'] = product_form
    context['product'] = product
    return render(request, "products/edit_product.html", context)

@login_required
@user_passes_test(is_librarian)
def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id = product_id)
    if not request.user.groups.filter(name='librarian').exists():
        return redirect("manage_products")
    product.delete()
    return redirect("manage")

def collections_view(request):
    context = get_context(request)
    query = request.GET.get('q', '')  # Get the search query
    collections = Collection.objects.all()

    if query:
        collections = collections.filter(
            Q(collection_name__icontains=query)
        )

    context['collections'] = collections
    context['query'] = query  # Pass the query to the context to retain it in the search box
    return render(request, "products/collections.html", context)

# def add_to_collections_view(request):
#     context = librarian(request)
#     if not request.user.is_authenticated:
#         return redirect('login')

#     if request.method == 'POST':
#         form = CollectionForm(request.POST, user=request.user)
#         if form.is_valid():
#             product = form.cleaned_data['product']
#             collection_name = form.cleaned_data['collection_name']
#             current_collection = form.cleaned_data['current_collection']
#             is_private = form.cleaned_data.get('is_private', False)

#             if collection_name:
#                 collection, created = Collection.objects.get_or_create(
#                     collection_name=collection_name,
#                     creator=request.user,
#                     defaults={'is_private': is_private}
#                 )
#             else:
#                 collection = current_collection

#             if collection:
#                 collection.products.add(product)
#                 collection.is_private = is_private
#                 collection.save()
#                 return redirect('collections')
#     else:
#         form = CollectionForm(user=request.user)
#         context['form'] = form

#     return render(request, 'products/add_to_collections.html', context)

def add_to_collections_view(request):
    context = get_context(request)
    if not request.user.is_authenticated:
        return redirect('login')

    # product = None
    # product_id = request.GET.get('product_id') or request.POST.get('product')
    # if product_id:
    #     try:
    #         product = Product.objects.get(id=product_id)
    #         context['product'] = product
    #     except Product.DoesNotExist:
    #         product = None

    next_url = request.POST.get('next', 'collections')

    if request.method == 'POST':
        form = CollectionForm(request.POST, user=request.user)
        if form.is_valid():
            product = form.cleaned_data['product']
            collection_name = form.cleaned_data['collection_name']
            current_collection = form.cleaned_data['current_collection']
            is_private = form.cleaned_data.get('is_private', False)

            if collection_name:
                collection, created = Collection.objects.get_or_create(
                    collection_name=collection_name,
                    creator=request.user,
                    defaults={'is_private': is_private}
                )
            else:
                collection = current_collection

            if collection:
                collection.products.add(product)
                collection.is_private = is_private
                collection.save()

                if collection.is_private:
                    product.in_private_collection = True
                    product.save()

                return redirect(next_url)
    else:
        form = CollectionForm(user=request.user)

    context['form'] = form
    return render(request, 'products/add_to_collections.html', context)

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id, creator=request.user)
    if request.method == 'POST':
        if collection.is_private:
            for product in collection.products.all():
                private_collections_count = product.collections.filter(is_private=True).count()
                if private_collections_count == 1:
                    product.in_private_collection = False
                    product.save()

        collection.delete()
        return redirect('collections')
    return redirect('collections')

def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if request.method == 'POST':
        product_ids = request.POST.getlist('remove_products')
        for product_id in product_ids:
            product = Product.objects.filter(id=product_id).first()
            if product:
                collection.products.remove(product)
                # After removing, update the product's private status
                if not product.collections.filter(is_private=True).exists():
                    product.in_private_collection = False
                    product.save()
        collection.save()
    return redirect('collections')

@login_required
def request_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    collection.visibility_requests.add(request.user)
    return redirect('collections')

@login_required
def handle_access_request(request, collection_id, user_id):
    collection = get_object_or_404(Collection, id=collection_id)
    requester = get_object_or_404(User, id=user_id)

    if request.user != collection.creator and not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            collection.visibility_requests.remove(requester)
            collection.visible_to.add(requester)
        elif action == 'deny':
            collection.visibility_requests.remove(requester)

    return redirect('collections')

@login_required
@user_passes_test(is_librarian)
def manage_users_view(request):
    users = User.objects.all().exclude(id=request.user.id)
    context = get_context(request)
    users_with_roles = []
    for user in users:
        users_with_roles.append({
            'user': user,
            'is_librarian': user.groups.filter(name='librarian').exists()
        })

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        if action == "make_librarian":
            user.groups.add(Group.objects.get(name='librarian'))
            messages.success(request, f"{user.username} has been made a librarian.")
        elif action == "remove_librarian":
            user.groups.remove(Group.objects.get(name='librarian'))
            messages.warning(request, f"{user.username} has been removed from the librarian group.")
        user.save()
        return redirect('manage_users')

    context['users_with_roles'] = users_with_roles
    return render(request, "products/manage_users.html", context)



# @login_required
# def product_detail(request, product_id):
#     product = Product.objects.get(id=product_id)
#     reviews = product.reviews.all()  # Get all reviews for the product

#     if request.method == 'POST':
#         rating = request.POST.get('rating')
#         comment = request.POST.get('comment')

#         # Debugging log to verify review creation
#         print(f"Rating: {rating}, Comment: {comment}, User: {request.user.username}")

#         # Create a new review
#         Review.objects.create(
#             product=product,
#             user=request.user,
#             rating=rating,
#             comment=comment
#         )
#         print("Review created successfully!")

#         return redirect('borrow_product_view', product_id=product.id)  # Redirect to the product page after submission

#     return render(request, 'borrow_product_view.html', {'product': product, 'reviews': reviews})
