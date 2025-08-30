import os


# def dynamic_updload_path(base):
#     def path(instance, filename):
#         model_name = instance.__class__.__name__.lower()
#         if instance.pk:
#             return f"{base}/{model_name}/{instance.pk}/{filename}"
#         return f"{base}/{model_name}/temp"
#     return path


def dynamic_updload_path(instance, filename):
    model_name = instance.__class__.__name__.lower()
    if instance.pk:
        return f"{model_name}/{instance.pk}/{filename}"
    return f"{model_name}/temp"