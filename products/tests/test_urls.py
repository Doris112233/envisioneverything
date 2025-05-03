from django.test import SimpleTestCase
from django.urls import reverse, resolve
from products import views

class ProductsUrlsTests(SimpleTestCase):

    def test_browse_url_resolves(self):
        url = reverse('browse')
        self.assertEqual(resolve(url).func, views.browse_view)
        self.assertEqual(url, '/products/browse/')

    def test_borrow_url_resolves(self):
        product_id = 1
        url = reverse('borrow_product', args=[product_id])
        self.assertEqual(resolve(url).func, views.borrow_product_view)
        self.assertEqual(url, f'/products/borrow_product/{product_id}/')

    def test_manage_url_resolves(self):
        url = reverse('manage')
        self.assertEqual(resolve(url).func, views.manage_view)
        self.assertEqual(url, '/products/manage/')

    def test_add_product_url_resolves(self):
        url = reverse('add_product')
        self.assertEqual(resolve(url).func, views.add_product_view)
        self.assertEqual(url, '/products/add_product/')

    def test_edit_product_url_resolves(self):
        product_id = 1
        url = reverse('edit_product', args=[product_id])
        self.assertEqual(resolve(url).func, views.edit_product_view)
        self.assertEqual(url, f'/products/edit_product/{product_id}/')
        
        ## diff product id (test may be wrong, its too late...)
        product_id = 999
        url = reverse('edit_product', args=[product_id])
        self.assertEqual(resolve(url).func, views.edit_product_view)
        self.assertEqual(url, f'/products/edit_product/{product_id}/')

    def test_delete_product_url_resolves(self):
        product_id = 1
        url = reverse('delete_product', args=[product_id])
        self.assertEqual(resolve(url).func, views.delete_product_view)
       

        self.assertEqual(url, f'/products/delete_product/{product_id}')
        
        # diff produc id
        product_id = 999
        url = reverse('delete_product', args=[product_id])
        self.assertEqual(resolve(url).func, views.delete_product_view)
        self.assertEqual(url, f'/products/delete_product/{product_id}')