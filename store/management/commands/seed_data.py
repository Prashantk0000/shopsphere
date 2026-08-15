from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from datetime import timedelta
from decimal import Decimal
import random
import io

from PIL import Image, ImageDraw, ImageFont
from store.models import Category, Brand, Product, Coupon
from accounts.models import Customer


# Color palettes for different categories
CATEGORY_COLORS = {
    'Electronics': [(30, 60, 114), (0, 172, 238)],
    'Fashion': [(236, 0, 140), (252, 103, 103)],
    'Home & Kitchen': [(34, 139, 34), (144, 238, 144)],
    'Books': [(139, 69, 19), (222, 184, 135)],
    'Sports': [(255, 69, 0), (255, 165, 0)],
    'Beauty': [(186, 85, 211), (255, 182, 193)],
}


class Command(BaseCommand):
    help = "Seed ShopSphere with sample data"

    def _generate_product_image(self, name, category_name, width=600, height=600):
        """Generate a gradient placeholder image with product name using Pillow."""
        colors = CATEGORY_COLORS.get(category_name, [(100, 100, 100), (200, 200, 200)])
        c1, c2 = colors

        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add subtle pattern (diagonal lines)
        for i in range(-height, width + height, 40):
            draw.line([(i, 0), (i + height, height)], fill=(255, 255, 255, 30), width=1)

        # Add product icon circle
        cx, cy = width // 2, height // 2 - 40
        radius = 80
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255, 60),
            outline=(255, 255, 255),
            width=3
        )

        # Draw a simple shopping bag icon in the circle
        bag_x, bag_y = cx, cy
        draw.rectangle(
            [bag_x - 30, bag_y - 15, bag_x + 30, bag_y + 35],
            outline='white', width=3
        )
        draw.arc(
            [bag_x - 18, bag_y - 35, bag_x + 18, bag_y - 5],
            start=180, end=0, fill='white', width=3
        )

        # Add product name text
        try:
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Product name (truncate if too long)
        display_name = name if len(name) <= 25 else name[:22] + "..."
        bbox = draw.textbbox((0, 0), display_name, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text(
            ((width - tw) // 2, height // 2 + 70),
            display_name,
            fill='white',
            font=font_large
        )

        # Category label
        bbox2 = draw.textbbox((0, 0), category_name, font=font_small)
        tw2 = bbox2[2] - bbox2[0]
        draw.text(
            ((width - tw2) // 2, height // 2 + 110),
            category_name,
            fill=(255, 255, 255, 180),
            font=font_small
        )

        # Save to ContentFile
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return ContentFile(buffer.getvalue())

    def _generate_category_image(self, name, width=800, height=400):
        """Generate a wider gradient banner for category."""
        return self._generate_product_image(name, name, width, height)

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # Superuser
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@shopsphere.com', 'admin123')
            admin.first_name = 'Admin'
            admin.save()
            profile, _ = Customer.objects.get_or_create(user=admin)
            profile.role = 'admin'
            profile.save()
            self.stdout.write(self.style.SUCCESS("  Admin created (admin / admin123)"))

        # Sample customer
        if not User.objects.filter(username='customer').exists():
            u = User.objects.create_user('customer', 'customer@shopsphere.com', 'customer123',
                                         first_name='John', last_name='Doe')
            Customer.objects.get_or_create(user=u, defaults={'role': 'customer'})
            self.stdout.write(self.style.SUCCESS("  Customer created (customer / customer123)"))

        # Categories
        categories_data = [
            ('Electronics', 'Latest gadgets and electronic devices'),
            ('Fashion', 'Clothing, shoes and accessories'),
            ('Home & Kitchen', 'Home essentials and kitchenware'),
            ('Books', 'Books across all genres'),
            ('Sports', 'Sports and outdoor equipment'),
            ('Beauty', 'Beauty and personal care products'),
        ]
        cats = []
        for name, desc in categories_data:
            c, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            if not c.image:
                self.stdout.write(f"  Generating image for category: {name}...")
                img_content = self._generate_category_image(name)
                c.image.save(f"{slugify(name)}.jpg", img_content, save=True)
            cats.append(c)

        # Brands
        brand_names = ['Acme', 'Sonic', 'Nova', 'Zenith', 'Peak', 'Vortex', 'Prime', 'Elite']
        brands = [Brand.objects.get_or_create(name=b)[0] for b in brand_names]

        # Products
        sample_products = [
            ('Wireless Bluetooth Headphones', 'Electronics', 2999, 1999, 'Premium noise-cancelling wireless headphones with 30hr battery life.'),
            ('Smart Watch Pro', 'Electronics', 8999, 6499, 'Fitness tracking, heart rate monitor, and always-on AMOLED display.'),
            ('4K Ultra HD Smart TV 43"', 'Electronics', 34999, 27999, 'Crystal-clear 4K resolution with HDR and built-in streaming apps.'),
            ('Wireless Mouse', 'Electronics', 799, 499, 'Ergonomic wireless mouse with silent clicks.'),
            ('Mechanical Keyboard RGB', 'Electronics', 4999, None, 'Cherry MX switches with per-key RGB backlighting.'),
            ("Men's Cotton T-Shirt", 'Fashion', 799, 499, '100% organic cotton, breathable and comfortable.'),
            ("Women's Denim Jacket", 'Fashion', 2499, 1799, 'Classic denim jacket for all seasons.'),
            ('Running Shoes', 'Fashion', 3499, 2499, 'Lightweight running shoes with cushioned soles.'),
            ('Leather Wallet', 'Fashion', 1299, None, 'Genuine leather bifold wallet with RFID protection.'),
            ('Non-Stick Cookware Set', 'Home & Kitchen', 4999, 3499, '7-piece non-stick cookware set with heat-resistant handles.'),
            ('Coffee Maker', 'Home & Kitchen', 6999, 4999, 'Programmable coffee maker with 12-cup capacity.'),
            ('Bedsheet Set (King Size)', 'Home & Kitchen', 1999, 1299, 'Soft microfiber bedsheet with 2 pillow covers.'),
            ('The Complete Python Programming', 'Books', 999, 699, 'Master Python from basics to advanced with 500+ examples.'),
            ('Atomic Habits', 'Books', 599, 399, 'The life-changing bestseller on building better habits.'),
            ('Yoga Mat Premium', 'Sports', 1499, 999, 'Non-slip 6mm thick yoga mat with carrying strap.'),
            ('Dumbbells Set 20kg', 'Sports', 3999, 2999, 'Adjustable dumbbells for home workouts.'),
            ('Football (Size 5)', 'Sports', 1299, 899, 'Official size and weight football, machine-stitched.'),
            ('Face Cream Moisturizer', 'Beauty', 899, 599, 'Hydrating face cream with vitamin E for all skin types.'),
            ('Hair Dryer Professional', 'Beauty', 2999, 1999, 'Salon-grade hair dryer with 3 heat settings.'),
            ('Lipstick Combo Pack', 'Beauty', 1499, 999, 'Set of 5 matte long-lasting lipsticks.'),
        ]

        created = 0
        for name, cat_name, price, disc, desc in sample_products:
            category = next((c for c in cats if c.name == cat_name), cats[0])
            brand = random.choice(brands)
            product, was_created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'brand': brand,
                    'description': desc,
                    'price': Decimal(price),
                    'discount_price': Decimal(disc) if disc else None,
                    'stock': random.randint(5, 50),
                    'is_available': True,
                    'is_featured': random.choice([True, False, False]),
                }
            )
            if was_created:
                created += 1

            # Generate product image if missing
            if not product.image:
                self.stdout.write(f"  Generating image for: {name}...")
                img_content = self._generate_product_image(name, cat_name)
                product.image.save(f"{slugify(name)}.jpg", img_content, save=True)

        self.stdout.write(self.style.SUCCESS(f"  {created} new products created"))
        self.stdout.write(self.style.SUCCESS(f"  Product images generated"))

        # Coupons
        if not Coupon.objects.filter(code='WELCOME10').exists():
            Coupon.objects.create(
                code='WELCOME10',
                discount_percent=10,
                active=True,
                valid_from=timezone.now() - timedelta(days=1),
                valid_until=timezone.now() + timedelta(days=90),
            )
        if not Coupon.objects.filter(code='SAVE20').exists():
            Coupon.objects.create(
                code='SAVE20',
                discount_percent=20,
                active=True,
                valid_from=timezone.now() - timedelta(days=1),
                valid_until=timezone.now() + timedelta(days=30),
            )
        self.stdout.write(self.style.SUCCESS("  Coupons created: WELCOME10 (10%), SAVE20 (20%)"))
        self.stdout.write(self.style.SUCCESS("\n  Seeding complete! Start with: python manage.py runserver"))

