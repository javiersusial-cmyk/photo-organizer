"""
Diccionario de monumentos/lugares famosos → ciudad.

CLIP compara la imagen contra estos prompts descriptivos. Si reconoce
un monumento icónico con suficiente confianza, asigna la ciudad
correspondiente — aunque la foto no tenga GPS ni nombre de carpeta.

IMPORTANTE: esto solo funciona con lugares VISUALMENTE DISTINTIVOS y
famosos. Una calle cualquiera no se reconoce. Los prompts están en
inglés porque CLIP rinde mejor en ese idioma.

Formato:  "prompt descriptivo del monumento": "Ciudad"
"""
from __future__ import annotations

LANDMARKS: dict[str, str] = {

    # ════════════════════════════════════════════════════════════════════════
    # ESPAÑA
    # ════════════════════════════════════════════════════════════════════════
    "the Peine del Viento wind comb sculpture by the sea":          "Donostia",
    "La Concha bay beach in San Sebastian":                         "Donostia",
    "the Guggenheim museum with titanium curves in Bilbao":         "Bilbao",
    "the Puppy flower sculpture in Bilbao":                         "Bilbao",
    "the Sagrada Familia basilica by Gaudi":                        "Barcelona",
    "Park Guell mosaic terrace by Gaudi":                          "Barcelona",
    "Casa Batllo colourful Gaudi facade":                          "Barcelona",
    "La Rambla street in Barcelona":                               "Barcelona",
    "Camp Nou football stadium Barcelona":                         "Barcelona",
    "the Puerta de Alcala stone gate in Madrid":                   "Madrid",
    "Plaza Mayor square in Madrid":                                "Madrid",
    "the Royal Palace of Madrid":                                  "Madrid",
    "Cibeles fountain and palace in Madrid":                       "Madrid",
    "the Giralda tower and cathedral in Seville":                  "Sevilla",
    "Plaza de Espana semicircular building in Seville":            "Sevilla",
    "the Royal Alcazar gardens of Seville":                        "Sevilla",
    "the Alhambra palace and fortress in Granada":                 "Granada",
    "the Mezquita mosque-cathedral of Cordoba":                    "Cordoba",
    "the City of Arts and Sciences futuristic buildings Valencia": "Valencia",
    "the cathedral of Santiago de Compostela":                     "Santiago_de_Compostela",
    "the Roman aqueduct of Segovia":                               "Segovia",
    "the Alcazar castle of Segovia":                               "Segovia",
    "the Alcazar fortress of Toledo on a hill":                    "Toledo",
    "the Basilica del Pilar by the river in Zaragoza":             "Zaragoza",
    "the cathedral of Palma de Mallorca by the sea":               "Mallorca",
    "the Roman theatre of Merida":                                 "Merida",
    "the hanging houses Casas Colgadas of Cuenca":                 "Cuenca",
    "the Alcazaba fortress of Malaga":                             "Malaga",
    "the Concatedral and old town of Caceres":                     "Caceres",
    "the walls and towers of Avila":                               "Avila",
    "the Mar de Cristal and old town of Cadiz":                    "Cadiz",

    # ════════════════════════════════════════════════════════════════════════
    # FRANCIA
    # ════════════════════════════════════════════════════════════════════════
    "the Eiffel Tower in Paris":                                   "Paris",
    "the Louvre glass pyramid in Paris":                           "Paris",
    "the Arc de Triomphe in Paris":                                "Paris",
    "Notre Dame cathedral in Paris":                               "Paris",
    "the Sacre Coeur basilica on Montmartre Paris":                "Paris",
    "the Palace of Versailles and gardens":                        "Versalles",
    "Mont Saint Michel abbey island":                              "Mont_Saint_Michel",
    "the medieval walled city of Carcassonne":                     "Carcassonne",
    "Notre-Dame de la Garde basilica overlooking Marseille":       "Marsella",
    "the Promenade des Anglais seafront in Nice":                  "Niza",
    "the Palais des Papes papal palace in Avignon":                "Avignon",
    "Strasbourg gothic cathedral and old town":                    "Estrasburgo",
    "the Chateau de Chambord renaissance castle":                  "Chambord",
    "the old town and basilica of Lyon":                           "Lyon",
    "Colmar colourful half-timbered canal houses":                 "Colmar",

    # ════════════════════════════════════════════════════════════════════════
    # ITALIA
    # ════════════════════════════════════════════════════════════════════════
    "the Colosseum amphitheatre in Rome":                          "Roma",
    "the Trevi Fountain in Rome":                                  "Roma",
    "Saint Peter's Basilica and square in the Vatican Rome":       "Roma",
    "the Pantheon dome in Rome":                                   "Roma",
    "the Roman Forum ancient ruins":                               "Roma",
    "Saint Mark's square and basilica in Venice":                  "Venecia",
    "the Rialto bridge over the Grand Canal Venice":               "Venecia",
    "gondolas on Venice canals":                                   "Venecia",
    "the Florence cathedral Duomo with red dome":                  "Florencia",
    "the Ponte Vecchio bridge in Florence":                        "Florencia",
    "the Leaning Tower of Pisa":                                   "Pisa",
    "the Milan cathedral Duomo gothic spires":                     "Milan",
    "the Galleria Vittorio Emanuele in Milan":                     "Milan",
    "the ruins of Pompeii with Vesuvius":                          "Pompeya",
    "the colourful cliffside houses of Amalfi coast":             "Amalfi",
    "the colourful houses of Cinque Terre on cliffs":             "Cinque_Terre",
    "the Roman arena amphitheatre of Verona":                      "Verona",
    "the Piazza del Campo shell-shaped square in Siena":          "Siena",
    "the trulli stone houses of Alberobello":                      "Alberobello",

    # ════════════════════════════════════════════════════════════════════════
    # PORTUGAL
    # ════════════════════════════════════════════════════════════════════════
    "the Belem Tower by the river in Lisbon":                      "Lisboa",
    "the Jeronimos monastery in Lisbon":                           "Lisboa",
    "the yellow tram 28 in Lisbon streets":                        "Lisboa",
    "the 25 de Abril suspension bridge in Lisbon":                 "Lisboa",
    "the Christ the King statue overlooking Lisbon":               "Lisboa",
    "the Dom Luis iron bridge in Porto":                           "Porto",
    "the Ribeira riverside colourful houses of Porto":             "Porto",
    "the Livraria Lello ornate bookshop in Porto":                 "Porto",
    "the colourful Pena Palace in Sintra":                         "Sintra",
    "the sanctuary of Fatima":                                     "Fatima",
    "the medieval walled town of Obidos":                          "Obidos",
    "the big waves and cliffs of Nazare":                          "Nazare",
    "the Roman temple of Evora":                                   "Evora",

    # ════════════════════════════════════════════════════════════════════════
    # REINO UNIDO
    # ════════════════════════════════════════════════════════════════════════
    "Big Ben clock tower and Houses of Parliament London":         "Londres",
    "Tower Bridge over the Thames in London":                      "Londres",
    "the London Eye ferris wheel":                                 "Londres",
    "Buckingham Palace in London":                                 "Londres",
    "St Paul's Cathedral dome in London":                          "Londres",
    "a red double-decker bus and telephone box in London":         "Londres",
    "Trafalgar Square and Nelson's column London":                 "Londres",
    "Edinburgh Castle on the rock":                                "Edimburgo",
    "the Roman Baths in the city of Bath":                         "Bath",
    "Stonehenge prehistoric stone circle":                         "Stonehenge",
    "the colleges and spires of Oxford":                           "Oxford",
    "the colleges and river of Cambridge":                         "Cambridge",
    "York Minster gothic cathedral":                               "York",

    # ════════════════════════════════════════════════════════════════════════
    # ESTADOS UNIDOS
    # ════════════════════════════════════════════════════════════════════════
    "the Las Vegas Strip with casinos and neon lights at night":   "Las_Vegas",
    "the Bellagio fountains in Las Vegas":                         "Las_Vegas",
    "the replica Eiffel Tower of the Paris casino Las Vegas":      "Las_Vegas",
    "the Welcome to Fabulous Las Vegas sign":                      "Las_Vegas",
    "the Venetian casino canals in Las Vegas":                     "Las_Vegas",
    "the New York New York casino skyline in Las Vegas":           "Las_Vegas",
}

# Umbral mínimo de confianza para aceptar un monumento.
# Más alto = más estricto (menos falsos positivos, pero pierde algunos).
#
# CLIP base concentra las puntuaciones en una banda estrecha (~0.25-0.30),
# así que este umbral es delicado:
#   0.27 → solo monumentos muy distintivos (Peine del Viento, Torre Eiffel...)
#   0.25 → más aciertos pero también falsos positivos (puentes, cuevas genéricas)
# Ajústalo según tus resultados.
LANDMARK_THRESHOLD = 0.27
