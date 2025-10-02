# Create Tools from OpenAPI Spec

QType allows you to automatically convert openapi specs to tools. This lets you make arbitrary calls in your flows, or connect them to agents.

This tutorial will walk you through creating convertting an openapi spec into QType specification that can be used in your applications.

## Prerequisites

Before following this tutorial, make sure you understand:

- [Variables and types](../../Concepts/variable.md) in QType
- [Primitive types](../../components/PrimitiveTypeEnum.md) 
- [Domain types](./domain-types.md)
- [Custom types](./custom-types.md)

## Overview

The `qtype convert api` command creates [tools](../../Concepts/tool.md), [AuthorizationProvider](../../Concepts/authorization-provider.md), and [Custom types](./custom-types.md) for each endpoint in the api.


## Converting the API to QType Tools

Via the QType  CLI:

```bash
qtype convert api spec.oas.yaml -o api_tools.qtype.yaml
```


