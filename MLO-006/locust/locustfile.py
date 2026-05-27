from locust import HttpUser, task, between
import random


class EmbeddingUser(HttpUser):
    # wait between 1 and 3 seconds between tasks (simulates real users)
    wait_time = between(0.5, 2)

    sentences = [
        "The sun rises.",
        "Quantum entanglement defies classical intuitions about locality.",
        "She forgot her umbrella.",
        "Migratory birds navigate thousands of miles using Earth's magnetic field as an internal compass.",
        "The bread burned.",
        "Ancient Mesopotamian civilizations developed early writing systems to track grain storage and trade.",
        "He laughed.",
        "Sleep deprivation significantly impairs cognitive function, emotional regulation, and immune response over time.",
        "The mountain was cold.",
        "A single honeybee visits up to 1,500 flowers to produce just one teaspoon of honey.",
        "Dogs bark at strangers.",
        "Plate tectonics slowly reshape continents over millions of years through subduction and seafloor spreading.",
        "The child cried loudly in the supermarket aisle.",
        "Jazz emerged from African American communities in New Orleans during the early twentieth century.",
        "Water boils at 100°C.",
        "The human gut microbiome contains trillions of microorganisms that directly influence mood, metabolism, and disease resistance.",
        "Traffic was terrible on Monday morning.",
        "Neurons fire.",
        "Philosophers have long debated whether free will is compatible with a deterministic universe governed by physical laws.",
        "The old library smelled of dust and forgotten stories.",
        "Inflation erodes purchasing power.",
        "She planted tomatoes along the southern fence every spring without fail, hoping this year the deer would leave them alone.",
        "Oceans absorb carbon dioxide.",
        "The discovery of penicillin by Alexander Fleming in 1928 revolutionized modern medicine and saved hundreds of millions of lives.",
        "He sold his car.",
    ]   

    @task(weight=3)  # more likely to be chosen than health_check
    def embed_text(self):
        self.client.post(
            "/embed",
            json={"text": random.choice(self.sentences)},
            headers={"Content-Type": "application/json"}
        )

    @task(weight=1)
    def health_check(self):
        self.client.get("/health/ready")

