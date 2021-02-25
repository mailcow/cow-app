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
            logger.error(f"Wrong value {value}")
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

    def _check_item (self, schema_key, schema, value):

        try:
            s_value = value.get(schema_key, None)
            if schema["required"] and s_value is None:
                logger.error(f"Missing arguments: {schema_key}")
                raise False

            elif not schema["required"] and  s_value is None or s_value == "":
                logger.warning(f"This item not requried, if you not use dont send {schema_key}")
                return True

            self._valid(schema, value.get(schema_key))

        except:
            raise False

    def is_valid (self, content):
        if self.schema:
            acceptable_sections = self.schema.keys()

            for section_name, section_value in content.items():

                if not section_name in acceptable_sections:
                    logger.error(f"Unacceptable section: {section_name}")
                    return False

                for schema_key, schema_value in self.schema[section_name].items():

                    try:
                        if type(section_value) is list:
                            for s_value in section_value:
                                self._check_item(schema_key, schema_value, s_value)
                        else:
                            self._check_item(schema_key, schema_value, section_value)
                    except:
                        return False

            return True

        return False
