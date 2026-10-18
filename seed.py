"""Seed script.

Run with:
    python seed.py            # add seed data (skips anything that already exists)
    python seed.py --reset    # drop and recreate all tables first, then seed
"""
import sys
from datetime import date
from decimal import Decimal

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Museum, User, Exhibition, MuseumVisit, MuseumReview, MuseumWishlist, ExhibitionVisit, ExhibitionReview, ExhibitionWishlist, MuseumPass, PassPrice, Ticket, DurationUnit


def reset_db():
    """Wipe all tables. Fine for early development with SQLite.

    Note: create_all() bypasses Alembic, so the alembic_version table is not
    touched. If you want the schema to come from migrations, delete museums.db
    and run `flask db upgrade` instead of using --reset.
    """
    db.drop_all()
    db.create_all()


def get_or_create(model, defaults=None, **lookup):
    """Return an existing row matching `lookup`, or create it.
    Keeps the script safe to run more than once."""
    instance = db.session.execute(
        db.select(model).filter_by(**lookup)
    ).scalar_one_or_none()
    if instance:
        return instance
    instance = model(**lookup, **(defaults or {}))
    db.session.add(instance)
    return instance

def seed_users():
    # Development-only passwords. Never reuse these anywhere real.
    admin = get_or_create(
        User,
        username="admin",
        defaults={
            "first_name": "admin",
            "last_name": "admin",
            "email": "admin@example.com",
            "password_hash": generate_password_hash("change-me"),
            "is_admin": True,
        },
    )
    alice = get_or_create(
        User,
        username="alice",
        defaults={
            "first_name": "Alice",
            "last_name": "Ficticio",
            "email": "alice@example.com",
            "password_hash": generate_password_hash("change-me"),
        },
    )
    return {"admin": admin, "alice": alice}

def seed_museums():
    museums = [
        {
            "name": "Museu do Aljube – Resistência e Liberdade",
            "country": "Portugal",
            "city": "Lisbon",
            "description": "Situado na antiga prisão do Aljube que, entre 1928 e 1965, funcionou como cárcere político do Estado Novo, tem como missão a preservação da memória do combate à ditadura e daqueles que lutaram pela liberdade e democracia.",
            "website": "https://www.museudoaljube.pt/en/",
            "image_url": "https://europeanmemories.net/wp-content/uploads/sites/19/2016/09/images.png",
            "address": "R. Augusto Rosa 42, 1100-059 Lisboa",
        },
        {
            "name": "Museu Nacional dos Coches",
            "country": "Portugal",
            "city": "Lisbon",
            "description": "O Museu Nacional dos Coches reúne uma coleção única no mundo de viaturas de gala e de passeio dos séculos XVI a XIX, na sua maioria provenientes da Casa Real Portuguesa, a que se acrescentaram veículos vindos dos bens da Igreja e de coleções particulares.",
            "website": "https://www.mncoches.gov.pt/en",
            "image_url": "https://media.timeout.com/images/103703334/750/422/image.jpg",
            "address": "Av. da Índia 136, 1300-300 Lisboa"
        },
    ]
    result = {}
    for data in museums:
        name = data["name"]
        defaults = {k: v for k, v in data.items() if k != "name"}
        result[name] = get_or_create(Museum, name=name, defaults=defaults)
    return result

def seed_museum_visits(users, museums):
    # Visit has a unique (user_id, museum_id, visit_date) constraint, so look up by both.
    get_or_create(
        MuseumVisit,
        user_id=users["alice"].id,
        museum_id=museums["Museu do Aljube – Resistência e Liberdade"].id,
        visit_date=date(2026, 5, 1)
    )

def seed_museum_wishs(users, museums):
    # Wish has a unique (user_id, museum_id) constraint, so look up by both.
    get_or_create(
        MuseumWishlist,
        user_id=users["alice"].id,
        museum_id=museums["Museu Nacional dos Coches"].id,
    )

def seed_museum_reviews(users, museums):
    # Review has a unique (user_id, museum_id) constraint, so look up by both.
    get_or_create(
        MuseumReview,
        user_id=users["alice"].id,
        museum_id=museums["Museu do Aljube – Resistência e Liberdade"].id,
        defaults={
            "rating": 4,
            "review": "Great collection, go early to avoid the crowds."
        }
    )

def seed_exhibitions():
    exhibitions = [
        {
            "museum_id": 1,
            "name": "Permanent exhibition",
            "short_description": "A Exposição Permanente do Museu apresenta aos visitantes uma caracterização geral do regime ditatorial português (1926-1974), os seus meios de opressão sobre a população (através da Censura e da ação repressiva das polícias e dos tribunais políticos), os meios de resposta das oposições, semi-legais e clandestinas, e ainda aspetos da luta anticolonial que induziu os militares ao derrube do regime por golpe militar, em 1974. No piso -1, os visitantes podem ainda ver parte das estruturas do edifício onde está alojado o Museu e uma mostra arqueológica levantada do seu subsolo.",
            "image_url": "https://europeanmemories.net/wp-content/uploads/sites/19/2016/09/images.png",
            "is_permanent": True,
        },
        {
            "museum_id": 1,
            "name": "Elas tiveram medo e foram",
            "short_description": "Quem foram? Como resistiram nas prisões? Como suportaram, quem as apoiou? Esta exposição tenta compreender melhor estas dimensões a partir das suas histórias de vida e continuar a aprofundar o conhecimento sobre este imenso património de resistência à ditadura.",
            "long_description": """Em 2021, a exposição temporária “Mulheres e Resistência – Novas Cartas Portuguesas e outras lutas” organizada pelo Museu do Aljube Resistência e Liberdade abordou diferentes expressões e momentos de resistência à ditadura a partir da vivência das mulheres. Agora, focamo-nos nas experiências das mulheres presas políticas. Quem foram? Como resistiram nas prisões? Como suportaram, quem as apoiou?

                                    Esta exposição tenta compreender melhor estas dimensões a partir das suas histórias de vida e continuar a aprofundar o conhecimento sobre este imenso património de resistência à ditadura. As mulheres resistiram à ditadura em todas as frentes. Algumas mergulharam na clandestinidade, viveram separadas das suas famílias e filhos durante anos a fio. Muitas outras foram presas e torturadas, algumas com os filhos. Outras exilaram e fugiram de um regime que as perseguia. Construíram redes de solidariedade poderosas e milhares abriram as portas das suas casas, acolheram e apoiaram generosamente antifascistas e as suas famílias. A longa e riquíssima história da resistência
                                    à ditadura não teria sido possível sem Elas.

                                    Aqui, nesta exposição temporária do Museu do Aljube Resistência e Liberdade, com início neste mês de março, prestamos profunda homenagem a todas elas, pela sua coragem, legado e inspiração.

                                    CURADORIA
                                    Rita Rato

                                    INVESTIGAÇÃO E TEXTOS
                                    Beatriz Tavares, Francisco Bairrão Ruivo e Rita Rato

                                    APOIO À INVESTIGAÇÃO
                                    Mariana Morgado e Hérika Cavalcante

                                    MURAIS
                                    Mariana, a miserável e Marta Nunes

                                    DESIGN PEÇA EXPOSITIVA
                                    Ricardo Carvalho Arquitectos & Associados – Nuno Gaspar

                                    DESIGN GRÁFICO
                                    Eduardo Ferreira

                                    PRODUÇÃO
                                    Ana Reguino e Joana Alves

                                    COMUNICAÇÃO
                                    Eduardo Ferreira, Joana Alves e Sara Borralho

                                    ORGANIZAÇÃO
                                    Museu do Aljube Resistência e Liberdade – Lisboa Cultura""",
            "website": "https://www.museudoaljube.pt/expo/elas-tiveram-medo-e-foram/",
            "image_url": "https://www.museudoaljube.pt/wp-content/uploads/2026/03/2026_03_NL_ET_Destaque.jpg",
            "is_permanent": False,
            "start_date": date(2026, 3, 11),
            "end_date": date(2027, 1, 31)
        },
        {
            "museum_id": 1,
            "name": "Antes de ser independência foi luta de libertação",
            "short_description": "Celebrar os 50 anos das independências explorando o arquivo do museu, e tentando gerar mais pensamento e ação anticolonial e antirracista, abolicionista de todas as formas de violência. ",
            "long_description": """Em 2022, nesta mesma sala, esteve patente a exposição temporária Ato (DES)colonial, pretendendo “questionar a herança colonial portuguesa durante o período da ditadura e valorizar as experiências de resistência anticolonial enquanto processos determinantes para as independências, mas igualmente para o derrube do fascismo em Portugal”.
                            Agora, celebrando os 50 anos das independências, recentramo-nos no nosso arquivo para continuar esta reflexão. Desde 2021 que tem avançado a descrição, digitalização e disponibilização dos fundos documentais doados ao nosso centro de documentação, e disponíveis na página eletrónica do Museu do Aljube – Arquivo Digital.
                            Antes de ser independência foi luta de libertação resulta de um trabalho de exploração destes fundos, desejando que gere mais pensamento e ação anticolonial e antirracista, abolicionista de todas as formas de violência.""",
            "website": "https://www.museudoaljube.pt/expo/antes-de-ser-independencia-foi-luta-de-libertacao/",
            "image_url": "https://www.museudoaljube.pt/wp-content/uploads/2025/03/2025_04_ReS_ET_Antes-de-Ser_Site-G.jpg",
            "is_permanent": False,
            "start_date": date(2025, 4, 3),
            "end_date": date(2026, 5, 31)
        },
        {
            "museum_id": 2,
            "name": "Permanent exhibition",
            "image_url": "https://media.timeout.com/images/103703334/750/422/image.jpg",
            "is_permanent": True,
        },
        {
            "museum_id": 2,
            "name": "Modelismo de Coches – José Cardoso Brito",
            "short_description": "Uma exposição dedicada ao extraordinário trabalho de recriação, em miniatura, de coches e outras viaturas históricas, que revela o rigor, a mestria e o elevado valor artístico da obra de José Brito.",
            "long_description": """O Museu Nacional dos Coches apresenta a exposição «Modelismo de Coches de José Brito», que reúne um conjunto de coches, carruagens, cadeirinhas e outras viaturas históricas construídos por José Brito à escala reduzida, maioritariamente 1:10. Com dimensões que variam entre os 50 e os 70 cm de comprimento, 30 e 40 cm de altura e 26 e 37 cm de largura, estas recriações distinguem-se pelo rigor histórico, pelo elevado grau de detalhe e pela qualidade técnica da sua execução.

                                Cada modelo resulta da conjugação de múltiplos elementos, cuidadosamente concebidos e executados, evidenciando o profundo conhecimento e a mestria de José Brito. O resultado é um conjunto de objetos artísticos de excecional valor, que preservam e divulgam a memória dos coches e de outras viaturas que marcaram a história dos transportes.

                                A exposição convida o público a descobrir um universo onde a precisão técnica, a investigação histórica e o saber-fazer artesanal se unem para dar vida a extraordinárias recriações em miniatura, revelando a riqueza de um métier raro e contribuindo para a valorização e divulgação do património ligado à história dos transportes.""",
            "website": "https://www.mncoches.gov.pt/agenda/modelismo-de-coches-jose-cardoso-brito",
            "image_url": "https://api.mncoches.pt/uploads/482275458_1039873058168037_3892780008366593794_n_1ed24d4482.jpg",
            "is_permanent": False,
        },
        {
            "museum_id": 2,
            "name": "Reis e Rainhas de Portugal, por Norberto Nunes",
            "short_description": "O Museu Nacional dos Coches apresenta ao público a exposição de pintura «Reis e Rainhas de Portugal», da autoria de Norberto Nunes.",
            "long_description": """Composta por 35 pinturas que retratam os reis e rainhas das quatro dinastias que governaram Portugal até 1910, a exposição convida os visitantes a revisitar, através da arte, algumas das figuras mais marcantes da monarquia portuguesa.
                                Patente na Galeria do Piso 2, esta proposta expositiva, simultaneamente lúdica e inesperada, promove um diálogo entre a pintura e o património histórico da coleção.""",
            "website": "https://www.mncoches.gov.pt/agenda/reis-e-rainhas-de-portugal-por-norberto-nunes",
            "image_url": "https://api.mncoches.pt/uploads/IMG_1115_e17f7da91e.jpg",
            "is_permanent": False,
        },
    ]
    result = {}
    for data in exhibitions:
        museum_id = data["museum_id"]
        name = data["name"]
        defaults = {k: v for k, v in data.items() if k not in ("museum_id", "name")}
        result[(museum_id, name)] = get_or_create(Exhibition, museum_id=museum_id, name=name, defaults=defaults)
    return result

def seed_exhibition_visits(users, exhibitions):
    # Visit has a unique (user_id, exhibition_id, visit_date) constraint, so look up by both.
    get_or_create(
        ExhibitionVisit,
        user_id=users["alice"].id,
        exhibition_id=1,
        visit_date=date(2026, 5, 1)
    )

def seed_exhibition_wishs(users, exhibitions):
    # Wish has a unique (user_id, exhibition_id) constraint, so look up by both.
    get_or_create(
        ExhibitionWishlist,
        user_id=users["alice"].id,
        exhibition_id=2,
    )

def seed_exhibition_reviews(users, exhibitions):
    # Review has a unique (user_id, exhibition_id) constraint, so look up by both.
    get_or_create(
        ExhibitionReview,
        user_id=users["alice"].id,
        exhibition_id=1,
        defaults={
            "rating": 4,
            "review": "Great collection, go early to avoid the crowds."
        }
    )

def seed_museum_pass():
    passes = [
        {
            "name": "Lisboa Card",
            "website": "https://www.visitlisboa.com/en/p/lisboa-card",
            "notes": "Includes free transportation in lisbon",
        },
        {
            "name": "COMBINADO: JERÓNIMOS, COCHES E AJUDA",
            "website": "https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches",
        },
        {
            "name": "COMBINADO: JERÓNIMOS E COCHES",
            "website": "https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches",
        },
        {
            "name": "COMBINADO: LISBOA REAL",
            "website": "https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches",
        },
    ]
    result = {}
    for data in passes:
        name = data["name"]
        defaults = {k: v for k, v in data.items() if k != "name"}
        result[name] = get_or_create(MuseumPass, name=name, defaults=defaults)
    return result

def seed_pass_prices(museum_passes):
    pass_prices = [
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Adult - 24h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 24,
        "price": 31,
        "currency": "EUR",
        "min_age": 16,
    },
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Child - 24h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 24,
        "price": 21,
        "currency": "EUR",
        "min_age": 4,
        "max_age": 15,
    },
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Adult - 48h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 48,
        "price": 51,
        "currency": "EUR",
        "min_age": 16,
    },
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Child - 48h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 48,
        "price": 28,
        "currency": "EUR",
        "min_age": 4,
        "max_age": 15,
    },
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Adult - 72h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 72,
        "price": 62,
        "currency": "EUR",
        "min_age": 16,
    },
    {
        "pass_id": museum_passes["Lisboa Card"].id,
        "label": "Child - 72h",
        "duration_unit": DurationUnit.hours,
        "duration_value": 72,
        "price": 35,
        "currency": "EUR",
        "min_age": 4,
        "max_age": 15,
    },
    {
        "pass_id": museum_passes["COMBINADO: JERÓNIMOS, COCHES E AJUDA"].id,
        "label": "Adult",
        "duration_unit": DurationUnit.days,
        "duration_value": 1,
        "price": 40,
        "currency": "EUR",
        "min_age": 25,
        "max_age": 65,
    },
    {
        "pass_id": museum_passes["COMBINADO: JERÓNIMOS, COCHES E AJUDA"].id,
        "label": "Young",
        "duration_unit": DurationUnit.days,
        "duration_value": 1,
        "price": 20,
        "currency": "EUR",
        "min_age": 13,
        "max_age": 24,
    },
    {
        "pass_id": museum_passes["COMBINADO: JERÓNIMOS, COCHES E AJUDA"].id,
        "label": "Senior",
        "duration_unit": DurationUnit.days,
        "duration_value": 1,
        "price": 20,
        "currency": "EUR",
        "min_age": 66,
    },
    ]
    for data in pass_prices:
        defaults = {k: v for k, v in data.items() if k not in ("pass_id", "label")}
        get_or_create(
            PassPrice,
            pass_id=data["pass_id"],
            label=data["label"],
            defaults=defaults
        )

def seed_tickets(museums, museum_passes):
    tickets = [
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Standard",
            "price": 4,
            "currency": "EUR",
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Young",
            "price": 2,
            "currency": "EUR",
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Senior",
            "price": Decimal("2.80"),
            "currency": "EUR",
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Child",
            "price": 0,
            "currency": "EUR",
            "max_age": 12,
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Young resident in municipality",
            "price": 0,
            "currency": "EUR",
            "resident_municipality": "Lisbon",
            "min_age": 13,
            "max_age": 23,
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Senior resident in municipality",
            "price": 0,
            "currency": "EUR",
            "resident_municipality": "Lisbon",
            "min_age": 65,
        },
        {
            "museum_id": museums["Museu do Aljube – Resistência e Liberdade"].id,
            "label": "Lisboa Card",
            "price": 0,
            "currency": "EUR",
            "pass_id": museum_passes["Lisboa Card"].id,
        },
    ]
    result = {}
    for data in tickets:
        museum_id = data["museum_id"]
        label = data["label"]
        defaults = {k: v for k, v in data.items() if k not in ("museum_id", "label")}
        result[(museum_id, label)] = get_or_create(Ticket, museum_id=museum_id, label=label, defaults=defaults)
    return result

def seed_ticket_exhibition(tickets, exhibitions, museums):
    pairs = [
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Standard"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Permanent exhibition")),
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Standard"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Elas tiveram medo e foram")),
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Standard"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Antes de ser independência foi luta de libertação")),
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Lisboa Card"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Permanent exhibition")),
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Lisboa Card"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Elas tiveram medo e foram")),
        ((museums["Museu do Aljube – Resistência e Liberdade"].id, "Lisboa Card"), (museums["Museu do Aljube – Resistência e Liberdade"].id, "Antes de ser independência foi luta de libertação")),
    ]
    for ticket_key, expo_key in pairs:
        ticket = tickets[ticket_key]
        expo = exhibitions[expo_key]
        if expo not in ticket.exhibitions:
            ticket.exhibitions.append(expo)

def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_db()

        users = seed_users()
        museums = seed_museums()
        exhibitions = seed_exhibitions()
        museum_passes = seed_museum_pass()
        # New rows have no id until they are flushed to the database.
        db.session.flush()

        tickets = seed_tickets(museums, museum_passes)
        db.session.flush()

        seed_museum_visits(users, museums)
        seed_museum_wishs(users, museums)
        seed_museum_reviews(users, museums)
        seed_exhibition_visits(users, exhibitions)
        seed_exhibition_wishs(users, exhibitions)
        seed_exhibition_reviews(users, exhibitions)
        seed_pass_prices(museum_passes)
        seed_ticket_exhibition(tickets, exhibitions, museums)

        db.session.commit()
        print("Seeding done.")


if __name__ == "__main__":
    main()