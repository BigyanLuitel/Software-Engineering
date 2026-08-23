from django.db import models


class School(models.Model):
    """
    Single-tenant config -- there should only ever be exactly ONE row
    in this table (see Option A decision from earlier in the project:
    this system serves one school, not a multi-tenant platform).
    """

    school_name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    contact_email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="school/", null=True, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    school_quote = models.CharField(max_length=300, blank=True, help_text="Optional school quote or motto")
    school_contact_number = models.CharField(max_length=20, blank=True, help_text="Optional school contact number")
    

    def __str__(self):
        return self.school_name

    def save(self, *args, **kwargs):
        """
        Enforces the single-row rule at the model level, not just by
        convention -- if a School row already exists and someone
        tries to create a second one, force it to overwrite the
        existing row instead of creating a duplicate. This protects
        against the exact mistake of accidentally ending up with two
        School rows and code elsewhere picking the "wrong" one.
        """
        if not self.pk and School.objects.exists():
            self.pk = School.objects.first().pk
        super().save(*args, **kwargs)