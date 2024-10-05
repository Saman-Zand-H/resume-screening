from django.contrib.postgres.fields import ArrayField
from django.db.models import CharField, Func, Transform
from django.db.models.fields import DateField, DateTimeField
from django.db.models.functions.datetime import (
    ExtractDay,
    ExtractHour,
    ExtractIsoYear,
    ExtractMinute,
    ExtractMonth,
    ExtractQuarter,
    ExtractSecond,
    ExtractWeek,
    ExtractWeekDay,
    ExtractYear,
)


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


DateTimeAge.register_lookup(ExtractYear)
DateTimeAge.register_lookup(ExtractMonth)
DateTimeAge.register_lookup(ExtractDay)
DateTimeAge.register_lookup(ExtractHour)
DateTimeAge.register_lookup(ExtractMinute)
DateTimeAge.register_lookup(ExtractSecond)
DateTimeAge.register_lookup(ExtractQuarter)
DateTimeAge.register_lookup(ExtractIsoYear)
DateTimeAge.register_lookup(ExtractWeek)
DateTimeAge.register_lookup(ExtractWeekDay)

DateAge.register_lookup(ExtractYear)
DateAge.register_lookup(ExtractMonth)
DateAge.register_lookup(ExtractDay)
DateAge.register_lookup(ExtractQuarter)
DateAge.register_lookup(ExtractIsoYear)
DateAge.register_lookup(ExtractWeek)
DateAge.register_lookup(ExtractWeekDay)
