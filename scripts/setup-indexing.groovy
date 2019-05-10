#!/usr/bin/env groovy

// EXAMPLE:
// ./setup-indexing.groovy 'path/to/conf/janusgraph-cql.properties'

@Grab('org.janusgraph:janusgraph-core:0.2.2')
@Grab('org.janusgraph:janusgraph-cql:0.2.2')
@Grab('org.janusgraph:janusgraph-es:0.2.2')
@GrabExclude('org.codehaus.groovy:*')
import org.apache.tinkerpop.gremlin.structure.Vertex
import org.janusgraph.core.Cardinality
import org.janusgraph.core.JanusGraphFactory
import org.janusgraph.core.schema.Mapping
import org.janusgraph.core.schema.SchemaAction
import org.janusgraph.core.schema.SchemaStatus
import org.janusgraph.graphdb.database.management.ManagementSystem

graph = JanusGraphFactory.open(args[0])
graph.tx().rollback()

m = graph.openManagement()
m.makePropertyKey('_uri').dataType(String.class).cardinality(Cardinality.SINGLE).make()
m.makePropertyKey('_created').dataType(Float.class).cardinality(Cardinality.SINGLE).make()
m.makePropertyKey('_processed').dataType(Float.class).cardinality(Cardinality.SINGLE).make()
m.commit()

m = graph.openManagement()
m.buildIndex('URI', Vertex.class)
        .addKey(m.getPropertyKey('_uri')).unique()
        .buildCompositeIndex()
m.buildIndex('CreatedProcessed',Vertex.class)
        .addKey(m.getPropertyKey('_created'))
        .addKey(m.getPropertyKey('_processed'))
        .buildMixedIndex("search")
m.commit()

ManagementSystem.awaitGraphIndexStatus(graph, 'URI').status(SchemaStatus.REGISTERED).call()
ManagementSystem.awaitGraphIndexStatus(graph, 'CreatedProcessed').status(SchemaStatus.REGISTERED).call()

m = graph.openManagement()
m.updateIndex(m.getGraphIndex('URI'), SchemaAction.REINDEX)
m.updateIndex(m.getGraphIndex('CreatedProcessed'), SchemaAction.REINDEX)
m.commit()

ManagementSystem.awaitGraphIndexStatus(graph, 'URI').status(SchemaStatus.ENABLED).call()
ManagementSystem.awaitGraphIndexStatus(graph, 'CreatedProcessed').status(SchemaStatus.ENABLED).call()

graph.close()
