#!/usr/bin/env groovy

//@Grab('org.slf4j:slf4j-simple:1.7.26')
@Grab('org.janusgraph:janusgraph-core:0.2.2')
@Grab('org.janusgraph:janusgraph-cql:0.2.2')
@Grab('org.janusgraph:janusgraph-es:0.2.2')
@GrabExclude('org.codehaus.groovy:*')
import org.apache.tinkerpop.gremlin.structure.Vertex
import org.janusgraph.core.Cardinality
import org.janusgraph.core.JanusGraphFactory
import org.janusgraph.core.schema.SchemaAction
import org.janusgraph.core.schema.SchemaStatus
import org.janusgraph.graphdb.database.management.ManagementSystem

graph = JanusGraphFactory.open('/home/mko/janusgraph-0.2.2-hadoop2/conf/janusgraph-cql.properties')
graph.tx().rollback()

m = graph.openManagement()
m.makePropertyKey('_uri').dataType(String.class).cardinality(Cardinality.SINGLE).make()
m.commit()

m = graph.openManagement()
m.buildIndex('_uri', Vertex.class).addKey(m.getPropertyKey('_uri')).unique().buildCompositeIndex()
m.commit()

ManagementSystem.awaitGraphIndexStatus(graph, '_uri').status(SchemaStatus.REGISTERED).call()

m = graph.openManagement()
m.updateIndex(m.getGraphIndex('_uri'), SchemaAction.REINDEX)
m.commit()

ManagementSystem.awaitGraphIndexStatus(graph, '_uri').status(SchemaStatus.ENABLED).call()

graph.close()
