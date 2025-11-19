import django_filters
from .models import Accessorym ,Accessoryl ,Laptop

class AccessorymFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description1 = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Accessorym
        fields = '__all__'
        exclude = ('price','price2','image','owner','description2' )

class AccessorylFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description1 = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Accessoryl
        fields = '__all__'
        exclude = ('price','price2','image','owner','description2' )

class LaptopFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description1 = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Laptop
        fields = '__all__'
        exclude = ('price','price2','image','owner','description2','image1' ,'image2' ,'image3' )


class AccessorymFilter2(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Accessorym
        fields = 'name',

class AccessorylFilter2(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Accessoryl
        fields = 'name',



