import os

from aws_cdk import App
from enum import Enum
from pydantic import BaseSettings, Field
from typing import Dict, Mapping, Any


def context_settings(settings: 'CdkSettings') -> Dict[str, Any]:
    """
    A settings source that searches the CDK Application's context for a value for each field in the settings.

    Requires the `Config` class of the settings object to have an `app` attribute set to an instantiated `aws_cdk.App`
    """
    settings_dict = {}
    for attr in settings.schema()['properties']:
        if settings.__config__.app.node.try_get_context(attr) is not None:
            settings_dict[attr] = settings.__config__.app.node.try_get_context(attr)
    return settings_dict


class ExportMode(Enum):
    ALWAYS = 'ALWAYS'
    IF_NOT_DEFAULT = 'IF_NOT_DEFAULT'
    IF_NOT_NONE = 'IF_NOT_NONE'
    NEVER = 'NEVER'


class CdkSettings(BaseSettings):
    """
    An extension of the pydantic.BaseSettings class that allows the aws_cdk.App to be supplied at instantiation so that
    the context variables can be used as a source.

    Additionally, it provides the following methods that make life simpler when working with CDK Pipelines:
    * `export_variables`
      A method that is used to get all variables that are flagged for "export" and returns them in a dictionary
      with their respective values. This is used primarily for providing values for the settings to the 'Synth' action
      in an AWS CodePipeline. As any settings with customised values supplied at runtime, will also need to be set
      within the environment of the 'Synth' CodeBuild project so that the custom values are retained and do not
      revert to their defaults.
    """
    class Config:
        app: App = None

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                context_settings,
                env_settings,
                file_secret_settings,
            )

    def __init__(self, app: App) -> None:
        self.__config__.app = app
        super(CdkSettings, self).__init__()

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
    account: str = Field(os.environ.get('CDK_DEFAULT_ACCOUNT'), export_mode=ExportMode.ALWAYS)
    region: str = Field(os.environ.get('CDK_DEFAULT_REGION'), export_mode=ExportMode.ALWAYS)

    class Config:
        env_prefix = 'cdk_'
