from cities_light.abstract_models import Base
from cities_light.models import City, Region

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "This command identifies regions and subregions without associated cities and creates new cities for them. "
        "The new cities will have the same name and data as the corresponding region or subregion."
    )

    def handle(self, *args, **kwargs):
        regions_without_cities = Region.objects.filter(city__isnull=True)
        self.stdout.write(self.style.SUCCESS(f"Found {regions_without_cities.count()} regions without cities."))
        common_fields = [f.name for f in Base._meta.get_fields()]

        cities_created_count = 0

        with transaction.atomic():
            for region in regions_without_cities:
                cities_created_count += self.process_region(region, common_fields)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Finished processing regions without cities. Total cities created: {cities_created_count}."
                )
            )

    def process_region(self, region, common_fields):
        cities_created_count = 0
        subregions_without_cities = region.subregion_set.filter(city__isnull=True)
        if subregions_without_cities.exists():
            for subregion in subregions_without_cities:
                cities_created_count += self.create_city_for_subregion(subregion, region, common_fields)
        else:
            cities_created_count += self.create_city_for_region(region, common_fields)
        return cities_created_count

    def create_city_for_subregion(self, subregion, region, common_fields):
        subregion_defaults = {
            **{field: getattr(subregion, field) for field in common_fields},
            "display_name": subregion.display_name,
            "country": subregion.country,
        }
        city, created = City.objects.get_or_create(
            subregion=subregion,
            region=region,
            defaults=subregion_defaults,
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Subregion: Created new city: {city} (ID: {city.id}) for subregion: {subregion} (ID: {subregion.id})"
                )
            )
            return 1
        return 0

    def create_city_for_region(self, region, common_fields):
        region_defaults = {
            **{field: getattr(region, field) for field in common_fields},
            "display_name": region.display_name,
            "country": region.country,
        }
        city, created = City.objects.get_or_create(region=region, defaults=region_defaults)
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Region: Created new city: {city} (ID: {city.id}) for region: {region} (ID: {region.id})"
                )
            )
            return 1
        return 0
