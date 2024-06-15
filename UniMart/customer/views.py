
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
import hashlib
from django.urls import reverse
from .models import Customer
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from django.db.models import Q
import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from .models import Product,Order,Cart,CartItem

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email)
        print(password)

        # Ensure email and password are not blank
        if email.strip() == '' or password.strip() == '':
            messages.error(request, 'Email and password cannot be blank.')
        else:
            try:
                customer = Customer.objects.get(email=email)
                # Compare hashed password with the provided password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()

                if customer.password == hashed_password:
                    # Store user email in session
                    request.session['customer_email'] = customer.email

                    # Determine redirection based on role and address presence
                    if customer.role == 'customer':
                        print("role-customer")
                        if customer.address.strip() == '':
                            return HttpResponseRedirect('address')  # Redirect to address page
                            print("taking customer address")
                        else:
                            print("redirecting to customer page")
                            return HttpResponseRedirect('user_dashboard')  # Redirect to user dashboard
                    elif customer.role == 'seller':
                        print("role-seller")
                        if customer.address.strip() == '':
                            print("taking seller address")
                            return HttpResponseRedirect('shopdetails')  # Redirect to shop details page
                        else:
                            print("getting seller dashboard")
                            return HttpResponseRedirect('seller_dashboard')  # Redirect to seller dashboard
                    else:
                        messages.error(request, 'Invalid role.')
                else:
                    messages.error(request, 'Invalid credentials. Please try again.')
            except Customer.DoesNotExist:
                messages.error(request, 'Customer does not exist. Please register.')

    return render(request, 'login.html', {'messages': messages.get_messages(request)})

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        mobile_number = request.POST.get('mobile')
        role = 'seller' if 'registerAsSeller' in request.POST else 'customer'

        # Ensure none of the fields are blank
        if name.strip() == '' or email.strip() == '' or password.strip() == '' or confirm_password.strip() == '':
            messages.error(request, 'All fields are required.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            if Customer.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
            else:
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                customer = Customer.objects.create(
                    name=name,
                    email=email,
                    password=hashed_password,
                    mobile_number=mobile_number,
                    role=role
                )
                messages.success(request, 'Registration successful. Please log in.')
                return HttpResponseRedirect('login')  # Redirect to the login page

    return render(request, 'register.html', {'messages': messages.get_messages(request)})

def address(request):
    # Retrieve customer email from session
    customer_email = request.session.get('customer_email', '')
    print("req")

    # Check if the email is present in session
    if not customer_email:
        messages.error(request, 'User email not found in session.')
        return redirect('login')  # Redirect to homepage or any error page

    try:
        # Fetch user based on email (assuming email is unique)
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer with this email does not exist.')
        return redirect('login')  # Redirect to homepage or any error page

    if request.method == 'POST':
        print("req")
        address = request.POST.get('address')

        if address.strip() == '':
            messages.error(request, 'Address cannot be blank.')
        else: # Assuming address field is in a profile model
            customer.save()  # Save the profile object (replace with appropriate model saving logic)

            messages.success(request, 'Address updated successfully.')
            return redirect('user_dashboard')  # Redirect to user dashboard page
    
    return render(request, 'address.html', {'messages': messages.get_messages(request)})
    

import re

def extract_file_id(url):
    # Extract the file ID from a Google Drive shareable link
    # Example input URL: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    pattern = r'/file/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None



# AWS S3 configuration
s3 = boto3.client('s3',
                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  region_name=settings.AWS_REGION_NAME)

BUCKET_NAME = settings.AWS_S3_BUCKET_NAME

def shopdetails(request):
    # Retrieve user email from session
    customer_email = request.session.get('customer_email', '')
    print(customer_email)

    # Check if the email is present in session
    if not customer_email:
        messages.error(request, 'Customer email not found in session.')
        return redirect('login')  # Redirect to login page or any error page
    
    # Get the user object based on the email
    try:
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')  # Redirect to login page or any error page

    if request.method == 'POST':
        shop_name = request.POST.get('shopName')
        shop_address = request.POST.get('shopAddress')
        shop_category = request.POST.get('shopcatagory')
        
        # Handle file upload
        shop_logo = request.FILES.get('shopLogo')
        if not shop_logo:
            messages.error(request, 'Shop logo is required.')
            return render(request, 'shopdetails.html', {'messages': messages.get_messages(request)})

        # Upload file to AWS S3
        try:
            s3.upload_fileobj(shop_logo, BUCKET_NAME, shop_logo.name)
            shop_logo_url = f'https://{BUCKET_NAME}.s3.amazonaws.com/{shop_logo.name}'
        except NoCredentialsError:
            messages.error(request, 'AWS credentials not available.')
            return render(request, 'shopdetails.html', {'messages': messages.get_messages(request)})

        # Update the user model with shop details
        customer.shop_name = shop_name
        customer.address = shop_address
        customer.shop_logo_url = shop_logo_url
        customer.shop_catagory = shop_category
        
        customer.save()
        
        messages.success(request, 'Shop details saved successfully.')
        return redirect('seller_dashboard')  # Redirect to user dashboard or any success page

    return render(request, 'shopdetails.html', {'messages': messages.get_messages(request)})

def user_dashboard(request):
    customer_email = request.session.get('customer_email', '')
    
    # Check if customer email is in session
    if not customer_email:
        messages.error(request, 'Customer email not found in session.')
        return redirect('login')  # Redirect to login page or any error page
    
    # Retrieve customer object based on the email
    try:
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer not found.')
        return redirect('login')  # Redirect to login page or any error page
    
    # Retrieve sellers who have a non-empty address
    sellers_with_addresses = Customer.objects.filter(role='seller', address__isnull=False)

    return render(request, 'user-dashboard.html', {
        'customer': customer,
        'seller_data': sellers_with_addresses
    })

def seller_dashboard(request):
    # Retrieve user email from session
    customer_email = request.session.get('customer_email', '')
    
    # Check if the email is present in session
    if not customer_email:
        messages.error(request, 'customer email not found in session.')
        return redirect('login')  # Redirect to login page or any error page
    
    # Get the customer object based on the email
    try:
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer not found.')
        return redirect('login')  # Redirect to login page or any error page
    
    # Assuming you want to pass user data to the template
    context = {
        'customer': customer
    }
    
    return render(request, 'seller_dashboard.html', context)




from django.shortcuts import render, redirect
from django.conf import settings
import boto3

def manage_products_ins(request):
    # Retrieve customer email from session
    customer_email = request.session.get('customer_email', '')

    try:
        # Fetch the Customer object based on the email from the session
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        # Handle case where customer does not exist or session data is invalid
        return redirect('login')  # Redirect to login page or handle appropriately

    if request.method == "POST":
        # Retrieve form data manually
        product_name = request.POST.get('productName')
        product_price = request.POST.get('productprice')
        product_unit = request.POST.get('productunit')
        product_description = request.POST.get('productdesc')
        uploaded_file = request.FILES.get('Productimage')

        if product_name and product_price and product_unit and product_description and uploaded_file:
            # Handle file upload to Amazon S3
            s3 = boto3.client('s3',
                              aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_REGION_NAME)
            
            # Upload file to S3 bucket
            bucket_name = settings.AWS_S3_BUCKET_NAME
            s3.upload_fileobj(uploaded_file, bucket_name, uploaded_file.name)
            
            # Create the S3 URL for the uploaded file
            photo_url = f"https://{bucket_name}.s3.amazonaws.com/{uploaded_file.name}"
            
            # Create a new instance of Product
            product_instance = Product(
                name=product_name,
                price=product_price,
                unit=product_unit,
                description=product_description,
                photo_url=photo_url,
                customer=customer
            )
            
            # Save the product instance
            product_instance.save()

            return redirect("manage_products_ins")

    # Fetch the existing products for the table
    manage_product_table_data = Product.objects.filter(customer=customer)

    return render(request, 'manage_products_ins.html', {
        'customer': customer,
        'manage_product_table_data': manage_product_table_data
    })


    
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Customer
import boto3
from django.conf import settings

def manage_products_upd(request, product_id):
    print("i am here")
    # Retrieve customer email from session
    customer_email = request.session.get('customer_email', '')

    try:
        # Fetch the Customer object based on the email from the session
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        # Handle case where customer does not exist or session data is invalid
        return redirect('login')  # Redirect to login page or handle appropriately
    print(customer.name)
    try:
        # Fetch the product based on product_id and customer
        product = Product.objects.get(id=product_id, customer=customer)
    except Product.DoesNotExist:
        # Handle case where product does not exist for the customer
        return HttpResponseNotFound("Product not found")  # Adjust error handling as needed
    print(product.name)
    if request.method == "POST":
        print("recieved request")
        # Retrieve form data manually
        product_name = request.POST.get('productName')
        product_price = request.POST.get('productprice')
        product_unit = request.POST.get('productunit')
        product_description = request.POST.get('productdesc')
        uploaded_file = request.FILES.get('Productimage')

        if product_name and product_price and product_unit and product_description:
            print("got all details")
            # Update product fields
            product.name = product_name
            product.price = product_price
            product.unit = product_unit
            product.description = product_description

            # Handle file upload to Amazon S3 if a new file is uploaded
            if uploaded_file:
                s3 = boto3.client('s3',
                                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                  region_name=settings.AWS_REGION_NAME)

                # Upload file to S3 bucket
                bucket_name = settings.AWS_S3_BUCKET_NAME
                s3.upload_fileobj(uploaded_file, bucket_name, uploaded_file.name)

                # Update photo_url with S3 URL
                product.photo_url = f"https://{bucket_name}.s3.amazonaws.com/{uploaded_file.name}"

            # Save the updated product instance
            product.save()
            print("saved details")

            return redirect("manage_products_ins")

    # Fetch the existing products for the table
    manage_product_table_data = Product.objects.filter(customer=customer)
    print("saved product details")

    return render(request, 'manage_products_upd.html', {
        'customer': customer,
        'product': product,  # Pass the product instance to pre-fill the form
        'manage_product_table_data': manage_product_table_data,  # Pass the product table data for rendering
    })

def manage_products_del(request, product_id):
    product_inst = Product.objects.get(id=product_id)
    product_inst.delete()
    messages.success(request,'Product deleted successfully!')
    return redirect("manage_products_ins")

def list_orders(request):
    # Get seller email from session
    seller_email = request.session.get('customer_email', '')
    
    if not seller_email:
        return redirect('login')  # Redirect to login if email not found in session
    
    # Get seller customer object
    seller = get_object_or_404(Customer, email=seller_email)
    
    # Filter orders by seller and order by order_date descending
    orders = Order.objects.filter(seller=seller).order_by('-id')
    
    return render(request, 'order_list.html', {'customer': seller, 'orders': orders})

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        status = request.POST.get('status')
        order.status = status
        order.save()
        return redirect('seller_dashboard')
def shop_details(request, id):
    seller = get_object_or_404(Customer, id=id, role='seller')
    products = Product.objects.filter(customer=seller)
    customer_email = request.session.get('customer_email', '')
    
    try:
        customer = Customer.objects.get(email=customer_email)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer not found.')
        return redirect('login')
    
    return render(request, 'shop_details.html', {
        'seller': seller,
        'products': products,
        'customer': customer,
    })
def product_details(request, id):
    # Fetch the product details using the provided id
    product = get_object_or_404(Product, id=id)

    # Render the product details template
    return render(request, 'product_details.html', {
        'product': product,
        'seller': product.customer,  # Assuming the Product model has a foreign key to the Shop model
    })
def add_to_cart(request, product_id_quantity):
    customer_email = request.session.get('customer_email', '')  # Get customer email from session
    customer = get_object_or_404(Customer, email=customer_email)  # Retrieve customer object

    # Extract product_id and quantity from the URL parameter
    product_id, quantity = map(int, product_id_quantity.split('-'))
    quantity=quantity
    product = get_object_or_404(Product, id=product_id)  # Retrieve product object

    # Ensure quantity is valid
    if quantity < 1:
        quantity = 1

    # Check if the customer already has a cart
    cart, created = Cart.objects.get_or_create(customer=customer)

    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)


    # Update the quantity of the cart item
    cart_item.quantity = quantity
    cart_item.save()

    # Redirect to cart view or product detail page
    return redirect(reverse('cart_view'))

    # If not a POST request, handle accordingly
    return redirect(reverse('home'))  # Redirect to home or previous pageem

def get_customer_from_session(request):
    customer_email = request.session.get('customer_email', '')
    customer = get_object_or_404(Customer, email=customer_email)
    return customer

from django.shortcuts import render
from .models import Cart, CartItem
from decimal import Decimal

def view_cart(request):
    customer = get_customer_from_session(request)
    cart, created = Cart.objects.get_or_create(customer=customer)

    if not cart.items.exists():
        # Handle case where cart is empty
        cart_items = []
        total_items = 0
        total_price = Decimal('0.00')  # Initialize total_price as Decimal
    else:
        cart_items = cart.items.all()
        total_items = cart.total_items()
        total_price = cart.total_price()

        # Calculate subtotal for each cart item
        for item in cart_items:
            item.subtotal = item.product.price * item.quantity

    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
    }

    return render(request, 'cart.html', context)

def get_customer_from_session(request):
    customer_email = request.session.get('customer_email', '')
    customer = get_object_or_404(Customer, email=customer_email)
    return customer
def edit_cart_item(request, cart_item_id_quantity):
    print(request)
    cart_item_id, quantity = map(int, cart_item_id_quantity.split('-'))
    cart_item = get_object_or_404(CartItem, pk=cart_item_id)
    print("wuant",quantity)


    if quantity > 0:
        cart_item.quantity=-cart_item.quantity
        print(cart_item.quantity)
        cart_item.quantity = quantity
        print(cart_item.quantity)
        cart_item.save()
    else:
        cart_item.delete()

        # Recalculate subtotal for each cart item
    cart_items = CartItem.objects.filter(cart=cart_item.cart)
    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
        item.save()

        # Calculate total price after updating quantities
    total_price = cart_item.cart.total_price()

        # Redirect back to cart view after processing


    return redirect('cart_view')
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, pk=cart_item_id)
    cart_item.delete()

    return redirect('cart_view')



def create_order_from_cart(request):
    # Step 1: Retrieve the customer from the session
    customer_email = request.session.get('customer_email')
    if not customer_email:
        # Handle case where customer email is not in session
        print("Customer email not found in session.")
        return redirect('home')  # Redirect to home or an appropriate page

    customer = get_object_or_404(Customer, email=customer_email)

    # Step 2: Retrieve the cart for the customer
    try:
        cart = Cart.objects.get(customer=customer)
    except Cart.DoesNotExist:
        print("You have no orders.")
        # Check if there are existing orders for the customer
        orders = Order.objects.filter(user=customer)
        if orders.exists():
            # Render the orders page if orders exist
            context = {
                'orders': orders,
            }
            return render(request, 'orders.html', context)
        else:
            # Render a template that says "No orders"
            return render(request, 'no_orders.html')

    # Step 3: Process each cart item
    cart_items = cart.items.all()
    
    orders_created = []  # Store the created orders

    for cart_item in cart_items:
        product = cart_item.product
        quantity = cart_item.quantity

        # Step 4: Create an order for each cart item
        order = Order.objects.create(
            user=customer,
            seller=product.customer,
            product=product,
            quantity=quantity,
            status='Pending'
        )

        # Add the created order to the list
        orders_created.append(order)

        # Delete the cart item
        cart_item.delete()

    # Step 5: Retrieve all orders for the customer (including newly created ones)
    orders = Order.objects.filter(user=customer)

    # Prepare the context for the template
    context = {
        'orders': orders,
    }

    # Render the orders summary page
    return render(request, 'orders.html', context)