from setuptools import setup

setup(
    data_files=[('subscription', ['subscription/utils/subscriptions.json'])],
    include_package_data=True,
)