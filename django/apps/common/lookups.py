from django.db.models import IntegerField, Transform
from django.db.models.fields import DateField, DateTimeField


class DeltaDays(Transform):
    lookup_name = "delta_days"
    output_field = IntegerField()

    def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)

        sql = f"EXTRACT(DAY FROM AGE(NOW(), {lhs}))"
        return sql, lhs_params


DateField.register_lookup(DeltaDays)
DateTimeField.register_lookup(DeltaDays)
