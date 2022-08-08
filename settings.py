import os

from aws_cdk import App
from enum import Enum
from pydantic import BaseSettings, Field
from typing import Mapping, Any


class ExportMode(Enum):
    ALWAYS = 'ALWAYS'
    IF_NOT_DEFAULT = 'IF_NOT_DEFAULT'
    IF_NOT_NONE = 'IF_NOT_NONE'
    NEVER = 'NEVER'


class CdkSettings(BaseSettings):
    """
    An extension of the pydantic.BaseSettings class that adds two methods which are specifically useful when
    creating a settings package for AWS CDK.

    * `update_from_context`
      A method that can be used to update values of settings based on the context items imported from the cdk.json,
      cdk.context.json file, or supplied to the CDK application as inline context items using `-c|--context`

    * `export_variables`
      A method that is used to get all variables that are flagged for "export" and returns them in a dictionary
      with their respective values. This is used primarily for providing values for the settings to the 'Synth' action
      in an AWS CodePipeline. As any settings with customised values supplied at runtime, will also need to be set
      within the environment of the 'Synth' CodeBuild project so that the custom values are retained and do not
      revert to their defaults.
    """

    def update_from_context(self, app: App) -> None:
        """Iterates through all of the keys that are present in the settings and attempts to retrieve a value
        from the CDK Application's context. If a value is found in context, it will replace any values that have been
        acquired from environment variables or a .env file.

        No prefix needs to be supplied to context variables in order to target their associated settings, in the event
        that a prefix is supplied in the settings configuration.
        """
        for key, value in self:
            if context_value := app.node.try_get_context(key):
                setattr(self, key, context_value)

    def export_variables(self) -> Mapping[str, Any]:
        """Iterates through all of the settings and locates any fields that have the 'export_mode' property, then
        returns them based on the value of the export mode and the value of the setting itself.

        To define a field with the 'export_mode' property, you have to define it on the settings class as a 'Field'.
        e.g.
            required_var: int = Field(..., export_mode=ExportMode.ALWAYS)
            var_with_default: str = Field('default_value', export_mode=ExportMode.IF_NOT_DEFAULT)
        """
        export_vars = {}

        # For each setting, if it should be exported then we add the setting to the export variables using
        # the first environment variable name for the setting in the schema. This was the prefix is included
        # and we will also use the correct name in the event an alias to unique environment variable name is
        # required for a particular setting field.
        for setting, setting_schema in self.schema()['properties'].items():
            if setting_schema.get('export_mode') == ExportMode.ALWAYS:
                export_vars[next(iter(setting_schema['env_names']))] = getattr(self, setting)

            elif setting_schema.get('export_mode') == ExportMode.IF_NOT_DEFAULT and \
                    getattr(self, setting) != setting_schema.get('default'):
                export_vars[next(iter(setting_schema['env_names']))] = getattr(self, setting)

            elif setting_schema.get('export_mode') == ExportMode.IF_NOT_NONE and getattr(self, setting) is not None:
                export_vars[next(iter(setting_schema['env_names']))] = getattr(self, setting)

            else:
                # Either export_mode is NEVER, or there is no export_mode property on the schema for this setting
                continue
        return export_vars


class Settings(CdkSettings):
    account: str = Field(os.environ['CDK_DEFAULT_ACCOUNT'], export_mode=ExportMode.ALWAYS)
    region: str = Field(os.environ['CDK_DEFAULT_REGION'])

    class Config:
        env_prefix = 'cdk_'


settings = Settings()
