from django.db import models

# Create your models here.
class Student(models.Model):
    name=models.CharField(max_length=30)
    birthdate=models.DateField()
    email=models.EmailField()

    def __str__(self):
        return '{} <{}>'.format(self.name,self.email)

class Course(models.Model):
    title=models.CharField(max_length=100)
    start_date=models.DateTimeField()
    end_date=models.DateTimeField()
    students=models.ManyToManyField(Student)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name='course'
        verbose_name_plural='courses'


