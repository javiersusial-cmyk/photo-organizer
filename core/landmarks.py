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
    "the medieval stone walls and towers of Avila":                "Avila",
    "the old town and cathedral of Cadiz by the sea":              "Cadiz",
    "the Plaza Mayor baroque square of Salamanca":                 "Salamanca",
    "the sandstone old town of Salamanca university":              "Salamanca",
    "the Burgos gothic cathedral spires":                          "Burgos",
    "the Leon gothic cathedral stained glass":                     "Leon",
    "the cathedral and Tower of Hercules in A Coruna":             "A_Coruna",
    "the Holy Grail cathedral of Valencia":                        "Valencia",
    "the Ciudad Encantada rock formations near Cuenca":            "Cuenca",
    "the Roman walls of Lugo":                                     "Lugo",
    "the cathedral of Murcia baroque facade":                      "Murcia",
    "the Castle of Santa Barbara overlooking Alicante":            "Alicante",
    "the white village houses of Mijas":                           "Mijas",
    "the El Caminito del Rey cliff walkway":                       "Malaga",
    "the white hilltop town of Ronda with its bridge":             "Ronda",
    "the cathedral and Roman bridge of Salamanca":                 "Salamanca",
    "the Monastery of El Escorial":                                "El_Escorial",
    "the cathedral of Leon with flying buttresses":                "Leon",
    "the Clerigos tower":                                          "Porto",
    "the Loyola sanctuary basilica":                              "Azpeitia",
    "the Mundaka surf wave and estuary":                           "Mundaka",
    "the San Juan de Gaztelugatxe island chapel and stairs":       "Bermeo",
    "the Bizkaia hanging transporter bridge":                      "Portugalete",
    "the Maria Cristina bridge and theatre in San Sebastian":      "Donostia",
    "the Kursaal cubes building in San Sebastian":                 "Donostia",
    "the Santa Maria del Naranco pre-romanesque church Oviedo":    "Oviedo",
    "the Gijon seaside and Cimadevilla old town":                  "Gijon",
    "the Santander bay and Magdalena palace":                      "Santander",
    "the Comillas Capricho house by Gaudi":                        "Comillas",
    "the Covadonga sanctuary and lakes in Picos de Europa":        "Covadonga",
    "the Pamplona running of the bulls San Fermin":                "Pamplona",
    "the Olite royal palace castle":                               "Olite",
    "the wine region and Marques de Riscal Gehry building":        "Logrono",

    # ── Francia (más) ────────────────────────────────────────────────────────
    "the Pont du Gard Roman aqueduct":                            "Avignon",
    "the calanques cliffs and harbour of Marseille":              "Marsella",
    "the Annecy canals and lake with mountains":                  "Annecy",
    "the Chamonix valley and Mont Blanc peak":                    "Chamonix",
    "the Dune du Pilat sand dune near Bordeaux":                  "Burdeos",
    "the Place de la Bourse and water mirror Bordeaux":           "Burdeos",
    "the pink city brick buildings of Toulouse":                  "Toulouse",
    "the Saint-Malo walled port town in Brittany":                "Saint_Malo",
    "the Rouen cathedral painted by Monet":                       "Rouen",
    "the Reims gothic coronation cathedral":                      "Reims",
    "the Nice old town and castle hill":                          "Niza",
    "the Cannes Croisette seafront and film festival":           "Cannes",
    "the medieval town of Rocamadour on a cliff":                "Rocamadour",
    "the Chateau de Chenonceau over the river":                  "Chenonceau",
    "the lavender fields of Provence":                           "Avignon",
    "the Disneyland Paris castle":                               "Paris",
    "the Pompidou centre colourful pipes Paris":                 "Paris",
    "the Moulin Rouge cabaret Paris":                            "Paris",
    "the Pantheon and Latin Quarter Paris":                      "Paris",

    # ── Italia (más) ─────────────────────────────────────────────────────────
    "the Spanish Steps in Rome":                                 "Roma",
    "the Castel Sant'Angelo fortress Rome":                      "Roma",
    "the Piazza Navona fountains Rome":                          "Roma",
    "the Bridge of Sighs in Venice":                             "Venecia",
    "the Burano colourful fishermen houses near Venice":         "Venecia",
    "the Boboli gardens and Pitti palace Florence":             "Florencia",
    "the Piazzale Michelangelo view of Florence":               "Florencia",
    "the Uffizi and Signoria square Florence":                   "Florencia",
    "the Sforza castle in Milan":                                "Milan",
    "the Last Supper and Navigli canals Milan":                  "Milan",
    "the blue grotto of Capri island":                           "Capri",
    "the Positano cliffside town Amalfi coast":                  "Positano",
    "the Sorrento cliffs over the bay of Naples":                "Sorrento",
    "the Mount Vesuvius volcano over Naples":                    "Napoles",
    "the Juliet balcony in Verona":                              "Verona",
    "the Lake Como villas and mountains":                        "Como",
    "the Sirmione castle on Lake Garda":                         "Sirmione",
    "the Matera ancient cave dwellings sassi":                   "Matera",
    "the Valley of the Temples Greek ruins Agrigento":           "Agrigento",
    "the Mount Etna volcano in Sicily":                          "Catania",
    "the Taormina Greek theatre over the sea":                   "Taormina",
    "the leaning towers of Bologna":                             "Bolonia",
    "the Trieste seafront Piazza Unita":                         "Trieste",
    "the Assisi basilica of Saint Francis on a hill":            "Asis",
    "the Lucca renaissance walls and towers":                    "Lucca",
    "the San Gimignano medieval towers skyline":                 "San_Gimignano",
    "the Dolomites mountain peaks":                              "Cortina_dAmpezzo",

    # ── Reino Unido (más) ────────────────────────────────────────────────────
    "the Shard glass skyscraper London":                        "Londres",
    "the Gherkin building London skyline":                       "Londres",
    "the Camden market and canals London":                       "Londres",
    "the Greenwich observatory and park London":                 "Londres",
    "the Royal Pavilion Indian palace in Brighton":              "Brighton",
    "the Brighton pier and beach":                               "Brighton",
    "the Liverpool waterfront and Liver building":               "Liverpool",
    "the Beatles and Albert Dock Liverpool":                     "Liverpool",
    "the Manchester town hall and industrial buildings":         "Manchester",
    "the Bristol Clifton suspension bridge":                     "Bristol",
    "the Durham cathedral and castle on the river":              "Durham",
    "the Canterbury cathedral":                                  "Canterbury",
    "the Windsor castle":                                        "Windsor",
    "the white cliffs of Dover":                                 "Dover",
    "the Roman wall and old town of Chester":                    "Chester",
    "the Snowdonia mountains in Wales":                          "Snowdonia",
    "the Cardiff castle and bay in Wales":                       "Cardiff",
    "the Loch Ness lake in the Scottish highlands":              "Inverness",
    "the Glenfinnan viaduct Harry Potter train":                "Fort_William",
    "the Isle of Skye fairy pools Scotland":                     "Skye",
    "the Glasgow Kelvingrove and cathedral":                     "Glasgow",
    "the Belfast Titanic museum":                                "Belfast",
    "the Giant's Causeway basalt columns Northern Ireland":      "Giants_Causeway",

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
