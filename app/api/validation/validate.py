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
            for v in value:

                if v == "field_type":
                    continue

                if schema["sub"]["field_type"] != dict:
                    if not schema["sub"]["rules"](v):
                        logger.error("Not validation")
                        raise False
                else:

                    if v not in schema["sub"].keys():
                        raise False

                    depth += 1
                    self._valid(schema["sub"], v, depth)

    def is_valid (self, content):
        if self.schema:
            acceptable_sections = self.schema.keys()
            for section_name, section_value in content.items():

                if not section_name in acceptable_sections:
                    logger.error("Unacceptable section")
                    raise False

                for schema_key, schema_value in self.schema[section_name].items():

                    try:
                        if schema_value["required"] and not section_value.get(schema_key):
                            logger.error("Missing arguments")
                            raise False

                        self._valid(schema_value, section_value)
                    except:
                        return False
            return True

        return False
