from django.db.models import Model, CharField, ForeignKey, ManyToManyField


class Moron(Model):
    name = CharField(max_length='100')


class Idiot(Model):
    name = CharField(max_length='100')


class Dummy(Model):
    name = CharField(max_length='100')
    moron = ForeignKey('Moron')
    idiots = ManyToManyField('Idiot')

class Simple(Model):
    name = CharField(max_length='100')
