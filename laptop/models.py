from django.db import models
from django.contrib.auth.models import User
# Create your models here.


def image_upload(instance,filename):
    imagename , extension = filename.split(".")
    return "homes/%s.%s"%(instance,extension)


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Category_accessoryl(models.Model):
    name= models.CharField(max_length=100)
    name2 = models.CharField(max_length=200)

    def __str__(self):
        return self.name2 
class Category_accessorym(models.Model):
    name= models.CharField(max_length=100)
    name2 = models.CharField(max_length=200)

    def __str__(self):
        return self.name2 

class Brand(models.Model):
    name= models.CharField(max_length=25)
    image = models.ImageField(upload_to=image_upload)

    def __str__(self):
        return self.name 


class Product(models.Model):
    name = models.CharField(max_length=200)
#b
    available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    code = models.BigIntegerField("الرقم التسلسلي", null=True, blank=True)

#    
    image = models.ImageField(upload_to=image_upload)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.name
    
#b
class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.user.username} - {self.product.name}"
#        
class Laptop(models.Model):
    brand = models.ForeignKey(Brand,on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    price2 = models.IntegerField()
    description1 = models.TextField(max_length=4000)
    description2 = models.TextField(max_length=4000)
#b
    available = models.BooleanField(default=True)
    code = models.BigIntegerField("الرقم التسلسلي", null=True, blank=True)

#
    image = models.ImageField(upload_to=image_upload)
    image1 = models.ImageField(upload_to=image_upload)
    image2 = models.ImageField(upload_to=image_upload)
    image3 = models.ImageField(upload_to=image_upload)

    def __str__(self):
        return self.name
    

class Accessoryl(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    price2 = models.IntegerField()
    description1 = models.TextField(max_length=4000)
    description2 = models.TextField(max_length=4000)
#b
    available = models.BooleanField(default=True)
    code = models.BigIntegerField("الرقم التسلسلي", null=True, blank=True)

#
    image = models.ImageField(upload_to=image_upload)
    category = models.ForeignKey(Category_accessoryl,on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Accessorym(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    price2 = models.IntegerField()
    description1 = models.TextField(max_length=4000)
    description2 = models.TextField(max_length=4000)
#b
    available = models.BooleanField(default=True)
    code = models.BigIntegerField("الرقم التسلسلي", null=True, blank=True)

#
    image = models.ImageField(upload_to=image_upload)
    category = models.ForeignKey(Category_accessorym,on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
