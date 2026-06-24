import { Database, Waypoints, DatabaseZap } from 'lucide-vue-next'

export const getKbTypeLabel = (type) => {
  const labels = {
    lightrag: 'LightRAG',
    milvus: 'CommonRAG',
    dify: 'Dify',
    text_rag: 'Text RAG',
    graph_rag: 'Graph RAG',
    visual_rag: 'Visual RAG'
  }
  return labels[type] || type
}

export const getKbTypeIcon = (type) => {
  const icons = {
    lightrag: Waypoints,
    milvus: DatabaseZap,
    dify: Database,
    text_rag: DatabaseZap,
    graph_rag: Waypoints,
    visual_rag: Database
  }
  return icons[type] || Database
}

export const getKbTypeColor = (type) => {
  const colors = {
    lightrag: 'purple',
    milvus: 'red',
    dify: 'gold',
    text_rag: 'red',
    graph_rag: 'purple',
    visual_rag: 'blue'
  }
  return colors[type] || 'blue'
}
