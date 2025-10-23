import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

from core.models import Product

products = Product.objects.all()
print(f'\nTotal products: {products.count()}\n')

for p in products:
    print(f'ID: {p.id}')
    print(f'Name: {p.name}')
    print(f'SKU: {p.sku}')
    print(f'Price: R{p.unit_price}')
    print(f'Active: {p.is_active}')
    print(f'Show on Website: {p.show_on_website}')
    print(f'Main Image: {p.main_image if p.main_image else "NO IMAGE"}')
    print(f'Image 2: {p.image_2 if p.image_2 else "NO IMAGE"}')
    print(f'Image 3: {p.image_3 if p.image_3 else "NO IMAGE"}')
    print(f'Image 4: {p.image_4 if p.image_4 else "NO IMAGE"}')
    print('-' * 50)

website_products = Product.objects.filter(is_active=True, show_on_website=True)
print(f'\nProducts for website: {website_products.count()}')
products_with_images = website_products.exclude(main_image='')
print(f'Products with images: {products_with_images.count()}')
for p in website_products:
    print(f'  - {p.name} (Image: {"YES" if p.main_image else "NO"})')
