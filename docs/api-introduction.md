# Introduction to the Apstra API
This section will give you an introduction to the Apstra API from an
organizational standpoint. The goal is to help you better understand how
the API is organized. We will also cover how to navigate and use the
documentation built into the Apstra system.

All Apstra usage and features are exposed with the Rest API. The User
Interface (UI) is also 100% built using the exposed API. So any workflow
you want to automate can be built with the API.

## API Organization
The Apstra API is broken down into two separate APIs, the Platform API and
the Reference Design API.

### Platform API
The Platform API includes endpoints that are used to manage the overall 
Apstra system or elements that reside outside of a Blueprint. 

If you need the element before creating a blueprint, the element can be
associated with multiple blueprints, or the element is not related to a 
blueprint then its located in the Platform API.

Examples would be:

- RBAC and user management
- Design resources
- System Agents
- Generic Blueprint Functionality

You will notice the Platform API has a number of Blueprint endpoints. 
These endpoints are generic endpoints used the same way in any type of 
Blueprint Design.
Examples would be:

- Blueprint Deploy (Commit Changes)
- Active Tasks
- Blueprint Nodes
- Blueprint Anomalies
- Graph queries

### Reference Design API (L3 Clos)
Apstra currently only supports one Reference Design, 
L3 Clos. The L3 Clos Reference Design API includes all endpoints used to 
build and manage a Blueprint in Apstra. 

## API Documentation and Tools
The API Documentation built into the Apstra product is located under 
Platform -> Developers on the main menu. Here you will see both the 
Platform and Reference Design API along with a number of Tools for working
with the API and Blueprint Graphs. 

### Swagger
Both APIs are documented with the OpenAPI spec using Swagger. From each
endpoint you have the capability to run and test the endpoint by clicking
the "Try it out" button. This will authenticate against Apstra using your
currently logged-in user.

Each endpoint provides a basic description and usage along with required
fields and payload model requirements. Standard return codes are also 
provided in the responses section.

### APIStraw and Rest API Explorer
You will see links for both APIStraw and Rest API Explorer under the tools
section. Both of these tools are included as an alternative way to search 
and navigate the Apstra api-specs.

### Graph Explorer
The Graph Explorer is used to run queries and search a Blueprint Graph. 
Graph Explorer provides a live document of the Blueprint Graph model. It
is also a good way to visually explore and get familar with graph queries. 

Graph Querys including examples are covered in the Solutions and Examples 
section under Blueprints [here](/example-scripts/blueprint/graph_queries/)