from django.forms import ModelForm
from django import forms
from .models import Borrow, Product, Collection

class ProductForm(ModelForm):
    product_name = forms.CharField()
    image = forms.ImageField()
    description = forms.CharField()
    price = forms.DecimalField()
    location = forms.CharField()
    category = forms.CharField()
    tag_name = forms.CharField(required=False, label="Tag (optional)")

    class Meta:
        model = Product
        fields = ['product_name', 'image', 'description', 'price', 'location', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tag:
            self.fields['tag_name'].initial = self.instance.tag.name

class CollectionForm(ModelForm):
    collection_name = forms.CharField(label="New Collection Name", required=False)
    current_collection = forms.ModelChoiceField(
        queryset=Collection.objects.none(),
        required=False,
        label="Select Existing Collection"
    )
    product = forms.ModelChoiceField(queryset=Product.objects.all(),
        required=True,
        label="Select a Product"
    )
    is_private = forms.BooleanField(
        required=False,
        label="Make Collection Private",
        initial=False
    )
    class Meta:
        model = Collection
        fields = ['collection_name', 'current_collection', 'product', 'is_private']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tag:
            self.fields['tag_name'].initial = self.instance.tag.nam
        if user:
            if user.groups.filter(name='librarian').exists():
                self.fields['current_collection'].queryset = Collection.objects.all()
            else:
                self.fields['current_collection'].queryset = Collection.objects.filter(creator=user)

                if not user.groups.filter(name='librarian').exists():
                    del self.fields['is_private']
