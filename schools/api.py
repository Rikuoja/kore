from rest_framework import routers, viewsets, mixins, filters
import django_filters
from django import forms
from rest_framework.exceptions import ParseError
from drf_cached_instances.mixins import CachedViewMixin
from .serializers import *
from schools import cache


class LanguageViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(Language)
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class SchoolTypeNameViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(SchoolTypeName)
    queryset = SchoolTypeName.objects.all()
    serializer_class = SchoolTypeNameSerializer
    paginate_by = 50


class SchoolFieldNameViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(SchoolFieldName)
    queryset = SchoolFieldName.objects.all()
    serializer_class = SchoolFieldNameSerializer


class InclusiveFilter(django_filters.Filter):
    """
    Filter for including entries where the field is null
    """

    def filter(self, qs, value):
        originalqs = super().filter(qs, value)
        self.lookup_type = 'isnull'
        nullqs = super().filter(qs, value)
        return nullqs | originalqs


class InclusiveNumberFilter(InclusiveFilter):
    field_class = forms.DecimalField


class NameOrIdFilter(django_filters.Filter):
    """
    Filter that switches search target between name and "id", depending on input
    """
    table, underscore, column = "", "", ""

    def filter(self, qs, value):
        if str(value).isdigit():
            self.field_class = forms.DecimalField
            if not self.column:
                # store table and column name
                self.table, self.underscore, self.column = self.name.rpartition('__')
            # overwrite column name with column id
            self.name = self.table + '__id'
        else:
            self.field_class = forms.CharField
            if self.column:
                # overwrite column id with column name
                self.name = self.table + '__' + self.column
        return super().filter(qs, value)


class GenderFilter(django_filters.CharFilter):
    """
    Filter that maps letters m, f and c to hard-coded genders
    """

    GENDER_MAP = {
        'm': 'poikakoulu',
        'f': 'tyttökoulu',
        'c': 'tyttö- ja poikakoulu'
    }

    def filter(self, qs, value):
        if value in ([], (), {}, None, ''):
            return qs
        val = str(value).lower()
        if val not in self.GENDER_MAP and val not in self.GENDER_MAP.values():
            raise ParseError("Gender must be 'm', 'f' or 'c' (for coed)")
        value = self.GENDER_MAP.get(val, val)
        return super().filter(qs, value)


class SchoolFilter(django_filters.FilterSet):
    # the end year can be null, so we cannot use a default filter
    from_year = InclusiveNumberFilter(name="names__end_year", lookup_type='gte')
    until_year = django_filters.NumberFilter(name="names__begin_year", lookup_type='lte')
    type = NameOrIdFilter(name="types__type__name", lookup_type='iexact')
    field = NameOrIdFilter(name="fields__field__description", lookup_type='iexact')
    language = NameOrIdFilter(name="languages__language__name", lookup_type='iexact')
    gender = GenderFilter(name="genders__gender", lookup_type='iexact')

    class Meta:
        model = School
        fields = ['type',
                  'field',
                  'language',
                  'gender',
                  'from_year',
                  'until_year']


class SchoolViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(School)
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    filter_class = SchoolFilter
    search_fields = ('names__types__value',)


class NameFilter(django_filters.CharFilter):
    """
    Filter that checks fields 'first_name' and 'surname'
    """
    table, underscore, column = "", "", ""

    def filter(self, qs, value):
        self.table, self.underscore, self.column = self.name.rpartition('__')
        if self.table:
            self.name = self.table + '__' + 'first_name'
        else:
            self.name = 'first_name'
        first_name_qs = super().filter(qs, value)
        if self.table:
            self.name = self.table + '__' + 'surname'
        else:
            self.name = 'surname'
        surname_qs = super().filter(qs, value)
        return first_name_qs | surname_qs


class ObligatoryNameFilter(NameFilter):
    """
    Filter that does not allow queries shorter than four characters
    """

    def filter(self, qs, value):
        if len(str(value)) < 4:
            raise ParseError("You must enter at least four characters in ?search=")
        return super().filter(qs, value)


class PrincipalFilter(django_filters.FilterSet):
    # the end year can be null, so we cannot use a default filter
    from_year = InclusiveNumberFilter(name="employers__end_year", lookup_type='gte')
    until_year = django_filters.NumberFilter(name="employers__begin_year", lookup_type='lte')
    # all principals may not be listed
    search = ObligatoryNameFilter(name="surname", lookup_type='icontains')
    school_type = NameOrIdFilter(name="employers__school__types__type__name", lookup_type='iexact')
    school_field = NameOrIdFilter(name="employers__school__fields__field__description", lookup_type='iexact')
    school_language = NameOrIdFilter(name="employers__school__languages__language__name", lookup_type='iexact')
    school_gender = GenderFilter(name="employers__school__genders__gender", lookup_type='iexact')

    class Meta:
        model = Principal
        fields = ['search',
                  'from_year',
                  'until_year',
                  'school_type',
                  'school_field',
                  'school_language',
                  'school_gender']


class EmployershipFilter(django_filters.FilterSet):
    # the end year can be null, so we cannot use a default filter
    from_year = InclusiveNumberFilter(name="end_year", lookup_type='gte')
    until_year = django_filters.NumberFilter(name="begin_year", lookup_type='lte')
    # all principals may not be listed
    search = ObligatoryNameFilter(name="principal__surname", lookup_type='icontains')
    school_type = NameOrIdFilter(name="school__types__type__name", lookup_type='iexact')
    school_field = NameOrIdFilter(name="school__fields__field__description", lookup_type='iexact')
    school_language = NameOrIdFilter(name="school__languages__language__name", lookup_type='iexact')
    school_gender = GenderFilter(name="school__genders__gender", lookup_type='iexact')

    class Meta:
        model = Employership
        fields = ['search',
                  'from_year',
                  'until_year',
                  'school_type',
                  'school_field',
                  'school_language',
                  'school_gender']


class SinglePrincipalViewSet(CachedViewMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    cache_class = cache.get_cache_class(Language)
    queryset = Principal.objects.all()
    serializer_class = PrincipalSerializer


class PrincipalViewSet(CachedViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Please enter principal name in ?search=
    """
    cache_class = cache.get_cache_class(Language)
    queryset = Principal.objects.all()
    serializer_class = PrincipalSerializer
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    filter_class = PrincipalFilter


class EmployershipViewSet(CachedViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Please enter principal name in ?search=
    """
    cache_class = cache.get_cache_class(Language)
    queryset = Employership.objects.all()
    serializer_class = EmployershipSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = EmployershipFilter


class AddressFilter(django_filters.CharFilter):
    """
    Filter that checks fields 'street_name_fi' and 'street_name_sv'
    """

    def filter(self, qs, value):
        self.name = 'building__buildingaddress__address__street_name_fi'
        street_name_fi_qs = super().filter(qs, value)
        self.name = 'building__buildingaddress__address__street_name_sv'
        street_name_sv_qs = super().filter(qs, value)
        return street_name_fi_qs | street_name_sv_qs


class SchoolBuildingFilter(django_filters.FilterSet):
    # the end year can be null, so we cannot use a default filter
    from_year = InclusiveNumberFilter(name="end_year", lookup_type='gte')
    until_year = django_filters.NumberFilter(name="begin_year", lookup_type='lte')
    search = AddressFilter(name="building__buildingaddress__address__street_name_fi", lookup_type='icontains')
    school_type = NameOrIdFilter(name="school__types__type__name", lookup_type='iexact')
    school_field = NameOrIdFilter(name="school__fields__field__description", lookup_type='iexact')
    school_language = NameOrIdFilter(name="school__languages__language__name", lookup_type='iexact')
    school_gender = GenderFilter(name="school__genders__gender", lookup_type='iexact')

    class Meta:
        model = SchoolBuilding
        fields = ['search',
                  'from_year',
                  'until_year',
                  'school_type',
                  'school_field',
                  'school_language',
                  'school_gender']


class BuildingFilter(django_filters.FilterSet):
    # the end year can be null, so we cannot use a default filter
    from_year = InclusiveNumberFilter(name="schools__end_year", lookup_type='gte')
    until_year = django_filters.NumberFilter(name="schools__begin_year", lookup_type='lte')
    search = AddressFilter(name="buildingaddress__address__street_name_fi", lookup_type='icontains')
    school_type = NameOrIdFilter(name="schools__school__types__type__name", lookup_type='iexact')
    school_field = NameOrIdFilter(name="schools__school__fields__field__description", lookup_type='iexact')
    school_language = NameOrIdFilter(name="schools__school__languages__language__name", lookup_type='iexact')
    school_gender = GenderFilter(name="schools__school__genders__gender", lookup_type='iexact')

    class Meta:
        model = Building
        fields = ['search',
                  'from_year',
                  'until_year',
                  'school_type',
                  'school_field',
                  'school_language',
                  'school_gender']


class SchoolBuildingViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(SchoolBuilding)
    queryset = SchoolBuilding.objects.all()
    serializer_class = SchoolBuildingSerializer
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    filter_class = SchoolBuildingFilter


class BuildingViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    cache_class = cache.get_cache_class(Building)
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    filter_class = BuildingFilter


router = routers.DefaultRouter()
router.register(r'school', SchoolViewSet)
router.register(r'principal', SinglePrincipalViewSet)
router.register(r'principal', PrincipalViewSet)
router.register(r'employership', EmployershipViewSet)
router.register(r'school_field', SchoolFieldNameViewSet)
router.register(r'school_type', SchoolTypeNameViewSet)
router.register(r'language', LanguageViewSet)
router.register(r'building', BuildingViewSet)
router.register(r'school_building', SchoolBuildingViewSet)
