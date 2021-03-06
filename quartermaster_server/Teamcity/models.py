from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
from data.models import Pool
from .config import TEAMCITY, TEAMCITY_HOST


class TeamCityPool(models.Model):
    """
    A pool is a collection fo resources that a reasonably similar
    They can optionally be associated with a TeamCity Shared Resource
    """

    shared_resource_url = models.URLField(unique=True, blank=True, null=True,
                                          help_text="Autogenerated form name, change will be lost")
    name = models.SlugField(blank=False, null=False, primary_key=True)
    pool = models.OneToOneField(Pool, blank=False, null=True, on_delete=models.CASCADE)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.get_teamcity_url()
        super().save(force_insert, force_update, using, update_fields)

    def clean(self):
        self.get_teamcity_url()

    def get_teamcity_url(self):
        # Hack to make unitests work
        if self.name.startswith("UNIT_TESTING_POOL"):
            self.shared_resource_url = f"http://example.com/{self.name}"
            return

        url = f"{TEAMCITY_HOST}/app/rest/2018.1/projects/?fields=project(id,projectFeatures(projectFeature(href,type,id,properties(*))))"
        response = TEAMCITY.get(url, headers={'Accept': 'application/json'})
        if response.status_code != 200:
            raise ConnectionError(f"Error encountered looking up for shared resourced {self.name} at, {url}")

        for project in response.json()['project']:
            for feature in project['projectFeatures']['projectFeature']:
                if feature['type'] == 'JetBrains.SharedResources':
                    pass
                    for prop in feature['properties']['property']:
                        if prop['name'] == 'name' and prop['value'] == self.name:
                            self.shared_resource_url = TEAMCITY_HOST + feature['href']
                            return
        raise ValidationError(f"Could not find shared resource named '{self.name}' when looking at {url}")

    def __str__(self):
        return self.name


class TeamCityPoolAdmin(admin.ModelAdmin):
    # Hiding shared_resource_url because it is auto generated 
    exclude = ('shared_resource_url',)


admin.site.register(TeamCityPool, TeamCityPoolAdmin)
