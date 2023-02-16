How to Deploy
=============

Services needed
---------------
You will need:
    - PostgreSQL database
    - RabbitMQ
    - Redis
    - An OIDC provider (Keycloak)

Services to deployed
--------------------
You will need to deploy 4 services:
    - static (nginx container spklabs/sentry-dynamic-sampling-controller-static)
    - Django API (spklabs/sentry-dynamic-sampling-controller)
    - Celery beat (alternative entrypoint in spklabs/sentry-dynamic-sampling-controller)
    - Celery Worker (alternative entrypoint in spklabs/sentry-dynamic-sampling-controller)



Docker-compose
--------------
You can find this docker-compose in the devops folder

.. literalinclude:: ../devops/docker-compose.example.yaml
    :language: yaml
