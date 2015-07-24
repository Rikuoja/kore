from rest_framework import serializers
from .models import *
from munigeo.api import GeoModelSerializer


class SchoolNameSerializer(serializers.ModelSerializer):
    official_name = serializers.CharField(allow_null=True, source='get_official_name')
    other_names = serializers.ListField(
        source='get_other_names',
        child=serializers.DictField(child=serializers.CharField())
    )

    class Meta:
        model = SchoolName
        exclude = ('school',)


class SchoolLanguageSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source='language.name')

    class Meta:
        model = SchoolLanguage
        exclude = ('school',)


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language


class SchoolTypeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolTypeName


class SchoolTypeSerializer(serializers.ModelSerializer):
    type = SchoolTypeNameSerializer()

    class Meta:
        model = SchoolType
        exclude = ('school',)


class SchoolFieldNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='description')

    class Meta:
        model = SchoolFieldName
        exclude = ('description',)


class SchoolFieldSerializer(serializers.ModelSerializer):
    field = SchoolFieldNameSerializer()

    class Meta:
        model = SchoolField
        exclude = ('school',)


class SchoolGenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolGender
        exclude = ('school',)


class SchoolNumberOfGradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberOfGrades
        exclude = ('school',)


class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood


class AddressLocationSerializer(GeoModelSerializer):
    class Meta:
        model = AddressLocation
        exclude = ('id', 'address')


class AddressSerializer(serializers.ModelSerializer):
    location = AddressLocationSerializer(required=False)

    def to_representation(self, obj):
        ret = super(AddressSerializer, self).to_representation(obj)
        if ret['location']:
            ret['location'] = ret['location']['location']
        return ret

    class Meta:
        model = Address


class DataTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataType


class ArchiveDataSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='link.url')
    data_type = DataTypeSerializer()

    class Meta:
        model = ArchiveData
        exclude = ('id',)


class OwnerFounderSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.description')

    class Meta:
        model = OwnerFounder


class SchoolOwnershipSerializer(serializers.ModelSerializer):
    owner = OwnerFounderSerializer()

    class Meta:
        model = SchoolOwnership
        exclude = ('school',)


class SchoolFounderSerializer(serializers.ModelSerializer):
    founder = OwnerFounderSerializer()

    class Meta:
        model = SchoolFounder
        exclude = ('school',)


class BuildingOwnershipSerializer(serializers.ModelSerializer):
    owner = OwnerFounderSerializer()

    class Meta:
        model = BuildingOwnership
        exclude = ('building',)


class BuildingForSchoolSerializer(serializers.ModelSerializer):
    neighborhood = serializers.CharField(source='neighborhood.name')
    addresses = AddressSerializer(many=True)
    owners = BuildingOwnershipSerializer(many=True)

    class Meta:
        model = Building
        # fields must be declared here to get both id and url
        fields = ('url', 'id', 'neighborhood', 'addresses', 'construction_year',
                  'architect', 'architect_firm', 'property_number', 'sliced',
                  'comment', 'reference', 'approx', 'owners')


class SchoolBuildingPhotoSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        # we have to reformat the URL representation so that our API serves the corresponding photo URL
        # this method will have to be updated whenever Finna API changes!
        representation = super(SchoolBuildingPhotoSerializer, self).to_representation(instance)
        new_url = representation['url'].replace('.finna.fi/Record/', '.finna.fi/thumbnail.php?id=')
        if new_url != representation['url']:
            # take care we don't append to the url if it wasn't modified
            new_url += '&size=large'
        representation['url'] = new_url
        return representation

    class Meta:
        model = SchoolBuildingPhoto
        exclude = ('school_building',)


class PrincipalForSchoolSerializer(serializers.ModelSerializer):
    """
    This class is needed for the School endpoint
    """

    class Meta:
        model = Principal
        # fields must be declared here to get both id and url
        fields = ('url', 'id', 'surname', 'first_name',)


class EmployershipForSchoolSerializer(serializers.ModelSerializer):
    principal = PrincipalForSchoolSerializer()

    class Meta:
        model = Employership
        exclude = ('nimen_id',)

    def to_representation(self, instance):
        # censor recent principal names
        representation = super().to_representation(instance)
        try:
            if representation['begin_year'] > 1950:
                representation['principal']['surname'] = None
                representation['principal']['first_name'] = None
        except TypeError:
            # censor names if year unknown
            representation['principal']['surname'] = None
            representation['principal']['first_name'] = None
        return representation


class SchoolBuildingForSchoolSerializer(serializers.ModelSerializer):
    """
    This class is needed for the School and Principal endpoints
    """
    photos = SchoolBuildingPhotoSerializer(many=True)
    building = BuildingForSchoolSerializer()

    class Meta:
        model = SchoolBuilding
        depth = 5
        # fields must be declared to get both id and url
        fields = ('url', 'id', 'building', 'photos', 'approx_begin', 'approx_end',
                  'begin_day', 'begin_month', 'begin_year', 'end_day', 'end_month', 'end_year',
                  'ownership', 'reference',)


class SchoolforSchoolContinuumSerializer(serializers.HyperlinkedModelSerializer):
    names = SchoolNameSerializer(many=True)

    class Meta:
        model = School
        # fields must be declared here to explicitly include id along with url
        fields = ('url', 'id', 'names')


class SchoolContinuumActiveSerializer(serializers.HyperlinkedModelSerializer):
    target_school = SchoolforSchoolContinuumSerializer()

    def to_representation(self, instance):
        # translate joins and separations to English
        representation = super().to_representation(instance)
        representation['description'] = representation['description'].replace(
            'yhdistyy', 'joins').replace('eroaa', 'separates from')
        return representation

    class Meta:
        model = SchoolContinuum
        fields = ('active_school', 'description', 'target_school', 'day', 'month', 'year',
                  'reference',)


class SchoolContinuumTargetSerializer(serializers.HyperlinkedModelSerializer):
    active_school = SchoolforSchoolContinuumSerializer()

    def to_representation(self, instance):
        # translate joins and separations to English
        representation = super().to_representation(instance)
        representation['description'] = representation['description'].replace(
            'yhdistyy', 'joins').replace('eroaa', 'separates from')
        return representation

    class Meta:
        model = SchoolContinuum
        fields = ('active_school', 'description', 'target_school', 'day', 'month', 'year',
                  'reference',)


class LifecycleEventSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source='type.description')

    class Meta:
        model = LifecycleEvent
        fields = ('description', 'day', 'month', 'year', 'decisionmaker', 'additional_info')


class SchoolSerializer(serializers.HyperlinkedModelSerializer):
    names = SchoolNameSerializer(many=True)
    languages = SchoolLanguageSerializer(many=True)
    types = SchoolTypeSerializer(many=True)
    fields = SchoolFieldSerializer(many=True)
    genders = SchoolGenderSerializer(many=True)
    grade_counts = SchoolNumberOfGradesSerializer(many=True)
    buildings = SchoolBuildingForSchoolSerializer(many=True)
    owners = SchoolOwnershipSerializer(many=True)
    founders = SchoolFounderSerializer(many=True)
    principals = EmployershipForSchoolSerializer(many=True)
    archives = ArchiveDataSerializer(many=True, required=False)
    lifecycle_event = LifecycleEventSerializer(many=True, required=False)
    continuum_active = SchoolContinuumActiveSerializer(many=True, required=False)
    continuum_target = SchoolContinuumTargetSerializer(many=True, required=False)

    class Meta:
        model = School
        # fields must be declared here to explicitly include id along with url
        fields = ('url', 'id', 'names', 'languages', 'types', 'fields', 'genders',
                  'grade_counts', 'buildings', 'owners', 'founders', 'principals',
                  'special_features', 'wartime_school', 'nicknames', 'checked',
                  'archives', 'lifecycle_event', 'continuum_active', 'continuum_target')


class SchoolBuildingSerializer(serializers.HyperlinkedModelSerializer):
    photos = SchoolBuildingPhotoSerializer(many=True)
    school = SchoolSerializer()
    building = BuildingForSchoolSerializer()

    class Meta:
        model = SchoolBuilding
        depth = 5
        # fields must be declared to get both id and url
        fields = ('url', 'id', 'building', 'photos', 'school', 'approx_begin', 'approx_end',
                  'begin_day', 'begin_month', 'begin_year', 'end_day', 'end_month', 'end_year',
                  'ownership', 'reference',)


class EmployershipForPrincipalSerializer(serializers.ModelSerializer):
    school = SchoolSerializer()

    class Meta:
        model = Employership
        exclude = ('nimen_id',)


class PrincipalSerializer(serializers.ModelSerializer):
    employers = EmployershipForPrincipalSerializer(many=True)

    class Meta:
        model = Principal
        # depth required to get all related data
        depth = 5
        # fields must be declared to get both id and url
        fields = ('url', 'id', 'surname', 'first_name', 'employers')

    def to_representation(self, instance):
        # censor recent principal names
        representation = super().to_representation(instance)
        try:
            if representation['employers'][0]['begin_year'] > 1950:
                representation['surname'] = None
                representation['first_name'] = None
        except TypeError:
            # censor names if year unknown
            representation['surname'] = None
            representation['first_name'] = None
        except KeyError:
            # censor names if employer unknown
            representation['surname'] = None
            representation['first_name'] = None
        return representation


class EmployershipSerializer(EmployershipForSchoolSerializer):
    school = SchoolSerializer()

    class Meta:
        model = Employership
        exclude = ('nimen_id',)


class SchoolBuildingForBuildingSerializer(serializers.ModelSerializer):
    photos = SchoolBuildingPhotoSerializer(many=True)
    school = SchoolSerializer()

    class Meta:
        model = SchoolBuilding
        depth = 5
        # fields must be declared to get both id and url
        fields = ('url', 'id', 'photos', 'school', 'approx_begin', 'approx_end',
                  'begin_day', 'begin_month', 'begin_year', 'end_day', 'end_month', 'end_year',
                  'ownership', 'reference',)


class BuildingSerializer(serializers.ModelSerializer):
    neighborhood = serializers.CharField(source='neighborhood.name')
    addresses = AddressSerializer(many=True)
    schools = SchoolBuildingForBuildingSerializer(many=True)

    class Meta:
        model = Building
        exclude = ('photo',)

