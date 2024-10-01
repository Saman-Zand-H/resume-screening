from django.contrib.postgres.fields import ArrayField
from django.db.models import CharField, Func, Transform
from django.db.models.fields import DateField, DateTimeField


class GetKeysByValue(Func):
    arity = 2
    output_field = ArrayField(CharField())

    def __init__(self, json_field_name, value, **extra):
        super().__init__(json_field_name, value, **extra)

    def as_sql(self, compiler, connection, function=None, template=None):
        json_field = self.source_expressions[0]
        value = self.source_expressions[1]
        json_field_sql, json_field_params = compiler.compile(json_field)
        value_sql, value_params = compiler.compile(value)

        sql = f"""
            (
                SELECT COALESCE(ARRAY_AGG(key), ARRAY[]::TEXT[])
                FROM jsonb_each({json_field_sql})
                WHERE value::text = {value_sql}::text
            )
        """
        params = json_field_params + value_params
        return sql, params


@DateTimeField.register_lookup
class DateTimeAge(Transform):
    lookup_name = "age"
    output_field = DateTimeField()

    def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)

        sql = f"AGE(NOW(), {lhs})"
        return sql, lhs_params


@DateField.register_lookup
class DateAge(DateTimeAge):
    output_field = DateField()
