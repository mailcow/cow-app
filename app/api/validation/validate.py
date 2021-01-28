from app.logger import logger

MAX_DEPTH = 5

class CowValidate:

    def __init__(self):
        try:
            module_path = f"app.api.validation.schemas.{self.name}"
            module = __import__(module_path, fromlist=[self.name])
            self.schema = module.schema
        except:
            self.schema = None
            logger.error("Schema not found")

    def _valid (self, schema, value, depth=0):

        if depth > MAX_DEPTH:
            logger.warning(f"Dict is too deep. Exceeded the given value {MAX_DEPTH}")
            raise False

        if not schema["rules"](value):
            logger.error("Missing arguments")
            raise False

        if schema["field_type"] in [list, dict]:
            for sub_value in value:

                if schema["sub"]["field_type"] != dict:
                    if not schema["sub"]["rules"](sub_value):
                        logger.error("Not validation")
                        raise False
                else:
                    for sub_key in schema["sub"].keys():

                        if sub_key == "field_type":
                            continue

                        if sub_key in sub_value:
                            self._valid(schema["sub"][sub_key], sub_value[sub_key], depth)

                    depth += 1

    def is_valid (self, content):
        if self.schema:
            acceptable_sections = self.schema.keys()

            for section_name, section_value in content.items():

                if not section_name in acceptable_sections:
                    logger.error("Unacceptable section")
                    raise False

                for schema_key, schema_value in self.schema[section_name].items():

                    try:
                        if schema_value["required"] and section_value.get(schema_key, None) is None:
                            logger.error(f"Missing arguments: {schema_key}")
                            raise False

                        self._valid(schema_value, section_value.get(schema_key))
                    except:
                        return False
            return True

        return False
