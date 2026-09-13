import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import json
import uuid
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

class Memory:
    def __init__(self, config):
        self.engine = sa.create_engine(f"sqlite:///{config['memory']['db_path']}")
        self.Session = sessionmaker(bind=self.engine)
        with self.engine.connect() as conn:
            conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    objective TEXT,
                    task TEXT,
                    result TEXT,
                    success INTEGER
                )
            """))
            conn.commit()

        self.vector_client = PersistentClient(
            path=config["memory"].get("vector_store_path", "data/memory_vectors/")
        )
        self.vector_collection = self.vector_client.get_or_create_collection("episodes")
        self.embedder = SentenceTransformer(config["knowledge"]["embedding_model"])

    def add_episode(self, objective, task, result, success):
        episode_id = str(uuid.uuid4())
        session = self.Session()
        session.execute(
            sa.text("INSERT INTO episodes (id, objective, task, result, success) VALUES (:id, :obj, :task, :res, :suc)"),
            {"id": episode_id, "obj": objective, "task": json.dumps(task),
             "res": json.dumps(result), "suc": int(success)}
        )
        session.commit()

        text_to_embed = f"{objective} | {task.get('tool','')} {' '.join(task.get('arguments',[]))} -> {'Success' if success else 'Fail'}"
        embedding = self.embedder.encode([text_to_embed]).tolist()
        self.vector_collection.add(
            embeddings=embedding,
            documents=[text_to_embed],
            metadatas=[{"episode_id": episode_id, "objective": objective}],
            ids=[episode_id]
        )

    def get_related(self, objective_fragment, k=3):
        query_emb = self.embedder.encode([objective_fragment]).tolist()
        results = self.vector_collection.query(query_embeddings=query_emb, n_results=k)
        ids = results.get("ids", [[]])[0]
        if not ids:
            return ""
        placeholders = ",".join([f"'{i}'" for i in ids])
        with self.engine.connect() as conn:
            rows = conn.execute(sa.text(
                f"SELECT task, result, success FROM episodes WHERE id IN ({placeholders})"
            )).fetchall()
        snippets = []
        for task, result, success in rows:
            snippets.append(f"Task: {task}\nOutcome: {'Success' if success else 'Fail'}\nResult: {result}")
        return "\n---\n".join(snippets)

    async def close(self):
        pass