from django.shortcuts import render
from . models import Category, Product ,Brand,Laptop , Accessoryl ,Accessorym , Category_accessorym ,Category_accessoryl
from .filters import AccessorymFilter,AccessorylFilter,LaptopFilter,AccessorymFilter2,AccessorylFilter2
# Create your views here.
from django.contrib.auth.decorators import login_required

@login_required
def product(request):
    product = Product.objects.all()
    brand = Brand.objects.all()
    return render(request , 'laptop/index.html', {'product' : product , 'brand':brand }) 
#b
def profile_view(request):
    return render(request, 'accounts/profile.html')
#
def service_dark(request):
    product = Product.objects.all()
    brand = Brand.objects.all()
    return render(request , 'laptop/service_dark.html', {'product' : product , 'brand' : brand}) 

def about(request):
    brand = Brand.objects.all()
    return render(request , 'laptop/it_about.html',{'brand' : brand}) 

def laptop_shop(request):
    laptop_shop = Laptop.objects.all()
    myfilter = LaptopFilter(request.GET,queryset=laptop_shop)
    laptop_shop = myfilter.qs 
    return render(request , 'laptop/laptop_shop.html',{'laptop_shop' : laptop_shop ,'myfilter':myfilter}) 

def accessoryl(request):
    accessoryl = Accessoryl.objects.all()
    myfilter = AccessorylFilter(request.GET,queryset=accessoryl)
    accessoryl = myfilter.qs 

    return render(request , 'laptop/accessory_laptop.html',{'accessoryl' : accessoryl ,'myfilter':myfilter}) 

def accessorym(request):
    accessorym = Accessorym.objects.all()

    myfilter = AccessorymFilter(request.GET,queryset=accessorym)
    accessorym = myfilter.qs 

    return render(request , 'laptop/accessory_mobile.html',{'accessorym' : accessorym,'myfilter':myfilter}) 


def contact(request):
    return render(request , 'laptop/contact.html',) 


def laptop_details(request, id ):
    laptop_detail = Laptop.objects.get(id = id)
    images = [laptop_detail.image, laptop_detail.image1, laptop_detail.image2, laptop_detail.image3]
    images = [img.url for img in images if img]  # تجميع الروابط غير الفارغة

    return render(request , 'laptop/service_detail.html', {'laptop_detail' :laptop_detail,'images': images}) 

def accessl_details(request ,id):
    accessoryl_details = Accessoryl.objects.get(id = id)
    return render(request , 'laptop/accessoryl_detail.html', {'accessoryl_detail' : accessoryl_details}) 


def accessm_details(request , id):
    accessorym_details = Accessorym.objects.get(id = id)
    return render(request , 'laptop/accessorym_detail.html', {'accessorym_details' : accessorym_details}) 



def laptop_by_brand(request, brand_name):
    try:
        brand = Brand.objects.get(name=brand_name)
        laptops = Laptop.objects.filter(brand=brand)
    except Brand.DoesNotExist:
        laptops = []
        brand = None
    
    # استرداد جميع العلامات التجارية
    all_brands = Brand.objects.all()

    # تأكد من تمرير جميع العلامات التجارية للقالب
    return render(request, 'laptop/laptop_by-brands.html', {'brand': brand, 'laptops': laptops})





def products_by_category(request, category_name):
    products = []

    # تحقق من الفئة في نموذج Accessorym
    try:
        accessorym_category = Category_accessorym.objects.get(name=category_name)
        accessorym_products = Accessorym.objects.filter(category=accessorym_category)
        myfilter = AccessorymFilter2(request.GET, queryset=accessorym_products)
        accessorym_products = myfilter.qs 
        products.extend(accessorym_products)

    except Category_accessorym.DoesNotExist:
        pass

    # تحقق من الفئة في نموذج Accessoryl
    try:
        accessoryl_category = Category_accessoryl.objects.get(name=category_name)
        accessoryl_products = Accessoryl.objects.filter(category=accessoryl_category)
        myfilter = AccessorylFilter2(request.GET, queryset=accessoryl_products)
        accessoryl_products = myfilter.qs   
        products.extend(accessoryl_products)

    except Category_accessoryl.DoesNotExist:
        pass

    # تحقق من الفئة في نموذج Product
    try:
        category = Category.objects.get(name=category_name)
        product_items = Product.objects.filter(category=category)
        myfilter = AccessorylFilter2(request.GET, queryset=product_items)
        product_items = myfilter.qs 
        products.extend(product_items)

    except Category.DoesNotExist:
        pass

    # تحقق من الفئة في نموذج Laptop فقط إذا كانت الفئة لابتوبات
    if category_name == 'لابتوبات':  # أو الاسم المناسب لفئة اللابتوبات
        try:
            laptop = Laptop.objects.all()
            myfilter = LaptopFilter(request.GET, queryset=laptop)
            laptop = myfilter.qs   
            products.extend(laptop)

        except Laptop.DoesNotExist:
            pass

    return render(request, 'laptop/products_by_category.html', {'products': products, 'category_name': category_name, 'myfilter': myfilter})


def service_det_all(request, id):
    # تعريف المتغيرات لاحتواء الخدمات من الجداول المختلفة
    service_accessoryl = None
    service_accessorym = None
    service_laptop = None

    # محاولة جلب الإكسسوار من جدول Accessoryl
    try:
        service_accessoryl = Accessoryl.objects.get(id=id)
    except Accessoryl.DoesNotExist:
        pass

    # محاولة جلب الإكسسوار من جدول Accessorym
    try:
        service_accessorym = Accessorym.objects.get(id=id)
    except Accessorym.DoesNotExist:
        pass

    # محاولة جلب اللابتوب من جدول Laptop
    try:
        service_laptop = Laptop.objects.get(id=id)
    except Laptop.DoesNotExist:
        pass

    # جلب المنتجات بناءً على الفئة
    items = []
    service = None
    image_url = ""
    
    if service_accessoryl:
        service = service_accessoryl
        items = Accessoryl.objects.filter(category=service_accessoryl.category)
        image_url = request.build_absolute_uri(service_accessoryl.image.url)
    elif service_accessorym:
        service = service_accessorym
        items = Accessorym.objects.filter(category=service_accessorym.category)
        image_url = request.build_absolute_uri(service_accessorym.image.url)
    elif service_laptop:
        service = service_laptop
        items = Laptop.objects.filter(brand=service_laptop.brand)  # عرض لابتوبات من نفس العلامة التجارية
        image_url = request.build_absolute_uri(service_laptop.image.url)
    
    # عرض صفحة التفاصيل
    return render(request, 'laptop/service_det_all.html', {
        'items': items,
        'service': service,
        'image_url': image_url,
    })

