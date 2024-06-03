# Mock users
users = [
    {"id": "1", "name": "Alice"},
    {"id": "2", "name": "Bob"},
    {"id": "3", "name": "Charlie"}
]

# Mock movies
movies = [
    {"id": "m1", "title": "The Matrix", "year": 1999, "genre": "Sci-Fi"},
    {"id": "m2", "title": "The Godfather", "year": 1972, "genre": "Crime"},
    {"id": "m3", "title": "Inception", "year": 2010, "genre": "Sci-Fi"}
]

# Mock ratings
ratings = [
    {"user_id": "1", "movie_id": "m1", "rating": 5},
    {"user_id": "1", "movie_id": "m2", "rating": 3},
    {"user_id": "2", "movie_id": "m1", "rating": 4},
    {"user_id": "2", "movie_id": "m3", "rating": 5},
    {"user_id": "3", "movie_id": "m2", "rating": 4},
    {"user_id": "3", "movie_id": "m3", "rating": 4}
]



from neo4j import GraphDatabase

class MovieGraph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user(self, user_id, name):
        with self.driver.session() as session:
            session.write_transaction(self._create_user_node, user_id, name)

    def create_movie(self, movie_id, title, year, genre):
        with self.driver.session() as session:
            session.write_transaction(self._create_movie_node, movie_id, title, year, genre)

    def create_rating(self, user_id, movie_id, rating):
        with self.driver.session() as session:
            session.write_transaction(self._create_rating_relationship, user_id, movie_id, rating)

    @staticmethod
    def _create_user_node(tx, user_id, name):
        tx.run("CREATE (u:User {id: $user_id, name: $name})", user_id=user_id, name=name)

    @staticmethod
    def _create_movie_node(tx, movie_id, title, year, genre):
        tx.run("CREATE (m:Movie {id: $movie_id, title: $title, year: $year, genre: $genre})",
               movie_id=movie_id, title=title, year=year, genre=genre)

    @staticmethod
    def _create_rating_relationship(tx, user_id, movie_id, rating):
        tx.run("""
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        CREATE (u)-[:RATED {rating: $rating}]->(m)
        """, user_id=user_id, movie_id=movie_id, rating=rating)

# Initialize connection to Neo4j
graph = MovieGraph("bolt://localhost:7687", "neo4j", "password")

# Populate the database with mock data
for user in users:
    graph.create_user(user["id"], user["name"])

for movie in movies:
    graph.create_movie(movie["id"], movie["title"], movie["year"], movie["genre"])

for rating in ratings:
    graph.create_rating(rating["user_id"], rating["movie_id"], rating["rating"])

graph.close()


import streamlit as st
from neo4j import GraphDatabase

class MovieGraph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_recommendations(self, user_id):
        recommendations = []
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:RATED]->(m:Movie)
                WITH m, COLLECT(u) AS users
                MATCH (other:User)-[:RATED]->(m)
                WHERE NOT other.id = $user_id
                WITH other, COUNT(*) AS common_movies
                ORDER BY common_movies DESC
                LIMIT 5
                MATCH (other)-[:RATED]->(rec:Movie)
                WHERE NOT (u)-[:RATED]->(rec)
                RETURN rec.title AS recommendation
                LIMIT 10
            """, user_id=user_id)
            for record in result:
                recommendations.append(record["recommendation"])
        return recommendations

# Initialize connection to Neo4j
graph = MovieGraph("bolt://localhost:7687", "neo4j", "password")

st.title("Movie Recommendation System")

# User input for user ID
user_id = st.text_input("Enter User ID:", "")

if st.button("Get Recommendations"):
    if user_id:
        recommendations = graph.get_recommendations(user_id)
        if recommendations:
            st.write("Recommended Movies:")
            for movie in recommendations:
                st.write(movie)
        else:
            st.write("No recommendations found for this user.")
    else:
        st.write("Please enter a valid User ID.")

graph.close()
