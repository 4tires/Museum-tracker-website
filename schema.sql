BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO "alembic_version" VALUES('dd277935776b');
CREATE TABLE exhibition (
	id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	short_description TEXT, 
	long_description TEXT, 
	website VARCHAR(254), 
	image_url VARCHAR(254), 
	is_permanent BOOLEAN NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_permanent_wth_date CHECK (NOT is_permanent OR end_date IS NULL), 
	CONSTRAINT ck_exhibition_date_range CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date), 
	FOREIGN KEY(museum_id) REFERENCES museum (id), 
	CONSTRAINT uq_exhibition_museum_name UNIQUE (museum_id, name)
);
INSERT INTO "exhibition" VALUES(1,1,'Permanent exhibition','A Exposição Permanente do Museu apresenta aos visitantes uma caracterização geral do regime ditatorial português (1926-1974), os seus meios de opressão sobre a população (através da Censura e da ação repressiva das polícias e dos tribunais políticos), os meios de resposta das oposições, semi-legais e clandestinas, e ainda aspetos da luta anticolonial que induziu os militares ao derrube do regime por golpe militar, em 1974. No piso -1, os visitantes podem ainda ver parte das estruturas do edifício onde está alojado o Museu e uma mostra arqueológica levantada do seu subsolo.',NULL,NULL,'https://europeanmemories.net/wp-content/uploads/sites/19/2016/09/images.png',1,NULL,NULL);
INSERT INTO "exhibition" VALUES(2,1,'Elas tiveram medo e foram','Quem foram? Como resistiram nas prisões? Como suportaram, quem as apoiou? Esta exposição tenta compreender melhor estas dimensões a partir das suas histórias de vida e continuar a aprofundar o conhecimento sobre este imenso património de resistência à ditadura.','Em 2021, a exposição temporária “Mulheres e Resistência – Novas Cartas Portuguesas e outras lutas” organizada pelo Museu do Aljube Resistência e Liberdade abordou diferentes expressões e momentos de resistência à ditadura a partir da vivência das mulheres. Agora, focamo-nos nas experiências das mulheres presas políticas. Quem foram? Como resistiram nas prisões? Como suportaram, quem as apoiou?

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
                                    Museu do Aljube Resistência e Liberdade – Lisboa Cultura','https://www.museudoaljube.pt/expo/elas-tiveram-medo-e-foram/','https://www.museudoaljube.pt/wp-content/uploads/2026/03/2026_03_NL_ET_Destaque.jpg',0,'2026-03-11','2027-01-31');
INSERT INTO "exhibition" VALUES(3,1,'Antes de ser independência foi luta de libertação','Celebrar os 50 anos das independências explorando o arquivo do museu, e tentando gerar mais pensamento e ação anticolonial e antirracista, abolicionista de todas as formas de violência.','Em 2022, nesta mesma sala, esteve patente a exposição temporária Ato (DES)colonial, pretendendo “questionar a herança colonial portuguesa durante o período da ditadura e valorizar as experiências de resistência anticolonial enquanto processos determinantes para as independências, mas igualmente para o derrube do fascismo em Portugal”.
Agora, celebrando os 50 anos das independências, recentramo-nos no nosso arquivo para continuar esta reflexão. Desde 2021 que tem avançado a descrição, digitalização e disponibilização dos fundos documentais doados ao nosso centro de documentação, e disponíveis na página eletrónica do Museu do Aljube – Arquivo Digital.
Antes de ser independência foi luta de libertação resulta de um trabalho de exploração destes fundos, desejando que gere mais pensamento e ação anticolonial e antirracista, abolicionista de todas as formas de violência.

Rita Rato
Diretora do Museu do Aljube Resistência e Liberdade

Ficha Técnica

Curadoria: Rita Rato
Arquivo: Patrícia Cordeiro
Desenho Expositivo: Rita Rato e Eduardo Ferreira                                                    Design Gráfico: Eduardo Ferreira
Textos: Aurora Almada, Victor Barros, Kitty Furtado e Miguel de Barros
Produção: Ana Reguino e Joana Alves
Comunicação: Eduardo Ferreira, Joana Alves e Sara Borralho
Organização: Museu do Aljube Resistência e Liberdade – Lisboa Cultura
Apoio: Associação Tchiweka de Documentação; African Activist Archive.','https://www.museudoaljube.pt/expo/antes-de-ser-independencia-foi-luta-de-libertacao/','https://www.museudoaljube.pt/wp-content/uploads/2025/03/2025_04_ReS_ET_Antes-de-Ser_Site-G.jpg',0,'2025-04-03','2026-05-31');
INSERT INTO "exhibition" VALUES(4,2,'Permanent exhibition',NULL,NULL,NULL,'https://media.timeout.com/images/103703334/750/422/image.jpg',1,NULL,NULL);
INSERT INTO "exhibition" VALUES(5,2,'Modelismo de Coches – José Cardoso Brito','Uma exposição dedicada ao extraordinário trabalho de recriação, em miniatura, de coches e outras viaturas históricas, que revela o rigor, a mestria e o elevado valor artístico da obra de José Brito.','O Museu Nacional dos Coches apresenta a exposição «Modelismo de Coches de José Brito», que reúne um conjunto de coches, carruagens, cadeirinhas e outras viaturas históricas construídos por José Brito à escala reduzida, maioritariamente 1:10. Com dimensões que variam entre os 50 e os 70 cm de comprimento, 30 e 40 cm de altura e 26 e 37 cm de largura, estas recriações distinguem-se pelo rigor histórico, pelo elevado grau de detalhe e pela qualidade técnica da sua execução.

Cada modelo resulta da conjugação de múltiplos elementos, cuidadosamente concebidos e executados, evidenciando o profundo conhecimento e a mestria de José Brito. O resultado é um conjunto de objetos artísticos de excecional valor, que preservam e divulgam a memória dos coches e de outras viaturas que marcaram a história dos transportes.

A exposição convida o público a descobrir um universo onde a precisão técnica, a investigação histórica e o saber-fazer artesanal se unem para dar vida a extraordinárias recriações em miniatura, revelando a riqueza de um métier raro e contribuindo para a valorização e divulgação do património ligado à história dos transportes.','https://www.mncoches.gov.pt/agenda/modelismo-de-coches-jose-cardoso-brito','https://api.mncoches.pt/uploads/482275458_1039873058168037_3892780008366593794_n_1ed24d4482.jpg',0,NULL,NULL);
INSERT INTO "exhibition" VALUES(6,2,'Reis e Rainhas de Portugal, por Norberto Nunes','O Museu Nacional dos Coches apresenta ao público a exposição de pintura «Reis e Rainhas de Portugal», da autoria de Norberto Nunes.','Composta por 35 pinturas que retratam os reis e rainhas das quatro dinastias que governaram Portugal até 1910, a exposição convida os visitantes a revisitar, através da arte, algumas das figuras mais marcantes da monarquia portuguesa. Patente na Galeria do Piso 2, esta proposta expositiva, simultaneamente lúdica e inesperada, promove um diálogo entre a pintura e o património histórico da coleção.','https://www.mncoches.gov.pt/agenda/reis-e-rainhas-de-portugal-por-norberto-nunes',NULL,0,NULL,NULL);
INSERT INTO "exhibition" VALUES(7,3,'Presença Portuguesa na Ásia',NULL,'A estranheza primeiro e a curiosidade depois: foram estes os ingredientes que permitiram o diálogo intercultural que deu origem à introdução de temáticas e repertórios iconográficos originais de que são reflexo as obras de arte presentes na Exposição Presença Portuguesa na Ásia.

Assim, os objectos provenientes da Índia, produzidos a partir de modelos europeus, mas com técnicas e matérias-primas locais - para satisfazer, inicialmente, uma clientela eclesiástica e, mais tarde, encomendas das elites nobres e burguesas europeias - manifestam-se aqui nas alfaias litúrgicas, têxteis, ourivesaria, mobiliário, objectos de marfim, cofres, contadores, revelando o simbolismo e a simbiose das duas culturas. O mesmo se passou no Japão, onde os contactos estabelecidos entre japoneses e os primeiros portugueses, deram origem a uma manifestação artística única conhecida como "arte namban" de que os biombos, contadores, oratórios, capacete e estribos são exemplares eloquentes.

O grande fascínio exercido pelas culturas chinesa e nipónica, desde o século XVI, manteve-se até ao século XIX e inícios do século XX, junto dos intelectuais portugueses Camilo Pessanha e Manuel Teixeira Gomes, que se tornaram figuras de referência na arte de coleccionar. Ao recolherem objectos icónicos destas culturas - como pinturas de rolo, álbuns de pintura chinesa, trajes, objectos para letrados, frascos de rapé chineses, netsuke e tsubas japoneses - deixaram um legado notável que, graças à colaboração do Museu Nacional Machado de Castro pode ser visto no Museu do Oriente.

O notável núcleo de porcelanas produzidas na China constitui uma das referências do Museu do Oriente, tornando-o numa das instituições de referência no domínio das artes decorativas.','https://www.foriente.pt/detalhe.php?id=26F4A205-A55B-473F-A6D7-0FC959095D3D&area=exposicoes','https://orientestorage.blob.core.windows.net/imgs-thumbs/fef704f204787ca240844764e40057479c75f4de',1,NULL,NULL);
INSERT INTO "exhibition" VALUES(8,3,'Japão: Festas e rituais',NULL,'Ao longo do ano, realizam-se no Japão inúmeras festas e rituais tradicionais de natureza religiosa, de grande importância social e cultural. Com momentos cerimoniais solenes e outros de puro divertimento, têm origem sobretudo no Xintoísmo - antigo culto dos espíritos kami – a que se juntaram práticas do Budismo. 

A exposição Japão: Festas e Rituais dá a conhecer estas celebrações e o seu papel na sociedade japonesa, como eixos de construção de identidade e comunidade, da sua concepção do mundo e das forças que o movem.

Tão variadas quanto populares, estas festas são celebradas em santuários e templos mas também no espaço doméstico, em comunidades rurais bem como nas metrópoles. Nascem da coexistência natural de diferentes sistemas de crenças no Japão e partilham um mesmo aspecto: a importância do ritual. É através da sua prática que se assegura a harmonia entre homens, natureza e divindades, de que depende a prosperidade e o bem comum. Transmitidos ao longo de gerações, numa continuidade que liga presente e passado e se projecta no futuro, os rituais reforçam os laços de pertença entre os indivíduos e traduzem-se, hoje, em valores como cidadania, responsabilidade social, sustentabilidade humana e ambiental.

Através de mais de 1500 peças, expostas aqui pela primeira vez, Japão: Festas e Rituais guia-nos através do universo destas celebrações: o panteão das divindades e seus atributos, as principais festividades e seus contextos, práticas e objectos associados.

Partindo dos princípios do Xintoísmo e Budismo no Japão, a exposição convida a um périplo pelo calendário das celebrações anuais, de onde se destacam o Ano Novo e as festas dos Rapazes e das Raparigas, a par de ritos de purificação, protecção e funerários, cultos de fertilidade e cerimónias de final do ano.

Numa impressionante cenografia que integra recriações de altares e espaços de culto, a exposição apresenta objectos devocionais, estatuetas, gravuras, instalações multimédia, fotografia e vídeo.

Japão: Festas e Rituais convida a mergulhar neste elemento vital da identidade japonesa, onde convergem tradição e renovação, mundo físico e espiritualidade.

Em associação às comemorações dos 480 anos de amizade entre Japão e Portugal

Apoio institucional Embaixada de Portugal no Japão; Embaixada do Japão em Portugal

Colaboração Hitachi; Japan Foundation; Universidade Lusófona','https://www.foriente.pt/detalhe.php?id=A2D1E49F-B9F3-4E46-9461-2F6577D16279&area=exposicoes','https://orientestorage.blob.core.windows.net/imgs-thumbs/a77927d7e5fbd0a9f43ea720d88da601eb2dfc7f',0,'2023-05-18','2028-01-02');
INSERT INTO "exhibition" VALUES(9,3,'You, me, us [o, hau, ita; tu, eu, nós]',NULL,'O discurso artístico contemporâneo de Timor-Leste emergiu na década de 1980, sobretudo como forma de resistência, profundamente influenciada pelos acontecimentos históricos que marcaram o país, incluindo os cerca de 500 anos de colonização portuguesa, a invasão indonésia em 1975 e a conquista da independência em 2002.

Actualmente, grande parte da produção dos artistas visuais timorenses revela não só uma forte inclinação para a contemporaneidade, como também uma profunda ligação às crenças populares, mitos e tradições timorenses. De igual forma, a linguagem criativa timorense mantém uma relação estreita com o discurso artístico e cultural português devido à colonização. Esta influência é particularmente visível na prática artística desenvolvida pelas mulheres timorenses na área dos têxteis, onde o bordado — introduzido pelos portugueses — passou a integrar os motivos decorativos do tais, o tecido tradicional de Timor-Leste.

A exposição You, Me, Us [O, Hau, Ita; Tu, Eu, Nós], da artista visual timorense Maria Madeira, foca a relação entre as crenças ancestrais timorenses e o discurso cultural português. Através de 34 obras de pintura, desenho, colagem e instalação, Maria Madeira suscita reflexão e diálogo em torno da sua experiência pessoal enquanto mulher timorense refugiada em Portugal e migrante na Austrália, neta de timorenses e portugueses. A exposição visa celebrar, sensibilizar e centrar a ligação histórica, cultural e pessoal que existe entre “Tu, Eu e Nós” — isto é, entre Portugal e Timor-Leste. 

You, Me, Us [O, Hau, Ita; Tu, Eu, Nós] oferece uma perspectiva distinta e autoral sobre a arte e a cultura timorenses, de uma artista contemporânea cuja prática criativa atravessa diferentes contextos culturais.

Realizada em paralelo com uma residência artística no espaço Hangar em Lisboa e um programa de oficinas, conversas e visitas You, Me, Us [O, Hau, Ita; Tu, Eu, Nós] propõe identificar desafios e explorar soluções inovadoras que fortaleçam o entendimento intercultural e valorização mútua entre Timor-Leste e Portugal.

Esta exposição conta com o patrocínio de Secretary of State of Art and Culture (SEAC) of Timor-Leste e The Good Business Foundation.','https://www.foriente.pt/detalhe.php?id=ABC8E74E-D81A-4A5B-ACC3-E0F235623D08&area=exposicoes',NULL,0,'2026-08-14','2026-12-13');
INSERT INTO "exhibition" VALUES(10,3,'Invocar o silêncio | Equilíbrios bioculturais na indonésia',NULL,'O silêncio ocupa um espaço primordial nas estruturas antropológicas e ontológicas do ser humano em todas as sociedades e culturas. Praticado e experienciado de um modo introspetivo, meditativo e individual ou de um modo expressivo, performativo e coletivo, como acontece na tradição do Hinduísmo Indonésio, o silêncio assume-se como um ritual de silêncio ecológico e cósmico que atravessa a escala humana, individual, e cósmica, coletiva. Na Indonésia, o silêncio é experienciado como consequência de uma catarse do ruído e do caos cósmico, uma não-ação estabelecida para que a terra e o cosmos se regenerem, se equilibrem e se sincronizem, possibilitando uma harmonia entre os humanos, a harmonia com a natureza e a harmonia com a ordem cósmica e divina, designado no Hinduísmo Balinês como Tri Hita Karana. Estes equilíbrios bioculturais tornam-se expressamente manifestos na observação dos ritmos cíclicos dos rituais e das celebrações marcadas pela prática do silêncio, como o Nyepi, o Ano Novo Balinês, o Tapa Bisu javanês, o Ramadão e a oração (aṣ-Ṣalāh), praticada coletivamente pelos muçulmanos e orientada para uma conexão individual e espiritual com Allāh (الله). A estes ritmos juntam-se ainda as oferendas diárias colocadas às divindades nos altares e as práticas contínuas de meditação ao longo do dia que atravessam a diversidade das estruturas religiosas da Indonésia. 

Esta exposição convida os visitantes a experienciarem um silêncio meditativo, pausado e rítmico, numa imersão sobre os equilíbrios bioculturais e cósmicos através dos lugares de intercessão entre os humanos, a natureza e o espiritual e a refletir sobre a importância destes equilíbrios para uma vida plena.

Curadoria

Rui Oliveira Lopes [Museu das Convergências]

Sofia Campos Lopes [Museu do Oriente]

Exposição integrada no ciclo de programação O Museu Convida... [Museu do Oriente] e no projecto Museu das Convergências: Um Museu em Viagem','https://www.foriente.pt/detalhe.php?id=9D048A4D-FA8E-415D-8C62-6AB4D5B60C21&area=exposicoes','https://orientestorage.blob.core.windows.net/imgs-thumbs/bf0a54085aa262c96128881e666fa2e5868645d8',0,'2026-09-23','2026-12-13');
INSERT INTO "exhibition" VALUES(11,4,'Permanent exhibition','MACAM''s collection developed in two stages. 

In the first phase, which began in 1974, collector Armando Martins bought only Portuguese art, paying special attention to 20th century art movements. From the 2000s onwards, he decided to open up the collection to contemporary international art from the end of the 20th century, with a particular focus on the 21st century.','MACAM''s collection developed in two stages. 

In the first phase, which began in 1974, collector Armando Martins bought only Portuguese art, paying special attention to 20th century art movements. From the 2000s onwards, he decided to open up the collection to contemporary international art from the end of the 20th century, with a particular focus on the 21st century.

This exhibition, which occupies galleries 1 and 2 on the ground floor of the palace, is permanent, so as to guarantee continuous access to the relevant works of art history that characterise the MACAM collection. Occasionally, some works will be rotated.

On MACAM’s first anniversary, we bring together the four panels that José de Almada Negreiros created in 1913, for the Cunha Tailoring House, at the age of 20. The two paintings from the MACAM collection are joined by the two belonging to CAM-FCG, restoring the series to its original configuration.

Previously exhibited together in 1984 and 2014, the four panels are now reunited, offering the public the opportunity to experience this magnificent work in its formal and conceptual integrity.

Gallery 1 offers a journey through the history of Portuguese art, through exemplary works by renowned masters who have moulded our country''s artistic identity, such as José Malhoa, Almada Negreiros, Amadeo de Souza-Cardoso, Eduardo Viana, Santa-Rita, António Dacosta, Maria Helena Vieira da Silva, José de Guimarães, Júlio Pomar, Lourdes Castro, René Bértholo, Nadir Afonso - among others.

Discover, in a chronological journey, the evolution of Portuguese art from the end of the 19th century to the modernist movements that revolutionised the 20th century.

In the second part of the permanent exhibition, the journey continues with works of contemporary art, in an approach organised by various thematic nuclei, in which art becomes a bridge between cultures and generations. 

In a dialogue between Portuguese and foreign artists, there are works by Thomas Ruff, Michael Biberstein, Pedro Cabrita Reis, Rui Chafes, Rosângela Renó, John Baldessari, Juan Munoz, Paula Rego, Marina Abramovic, Elmgreen & Dragset, Fernanda Fragateiro, Isa Genzken, among others. 

In this part of the exhibition, you''ll find a multiplicity of artistic languages and media, such as photography, video and installation, which go beyond the traditional parameters of previous eras. Discover how contemporary art addresses issues such as globalisation and reflects new perspectives on our relationship with reality.','https://macam.pt/en/permanent-exhibition',NULL,1,NULL,NULL);
INSERT INTO "exhibition" VALUES(12,4,'Weight-Counter-Weight','Three-dimensional works from the MACAM Collection','Weight-Counter-Weight brings together a collection of three-dimensional works from the MACAM Collection that explore different forms of balance, tension, and transformation in space. Organized around thematic clusters – nature and abstraction, scale and resistance, cities and urbanism – the exhibition invites reflection on the forces that shape both the built and natural worlds. Through references to architecture, urban expansion, and the dynamics of collective life, the works reveal relationships of conflict, adaptation, and permanence. The tension between materials, forms, and scales highlights not only processes of physical, social, and symbolic resistance but also how the observation of nature inspires exercises in synthesis, abstraction, and formal reinvention. Through sculptures, installations, and other three-dimensional works, Portuguese and international artists explore concepts of weight and counterweight that extend far beyond the material dimension of the works.


Curated by Adelaide Ginga and Carolina Quintela

Spatial consulting: Cassandra Guimarães Carvas e Rita Aguiar Rodrigues','https://macam.pt/en/whats-on/weight-counter-weight-three-dimensional-works-from-the-macam-collection','https://cms.macam.pt/storage/uploads/thumbs/imagem-exposicao-peso-contra-peso_w1920.jpg',0,'2026-07-04','2027-03-29');
INSERT INTO "exhibition" VALUES(13,4,'Other Spaces (Fault line)','Photography in the Américo Marques Collection (Part II)','Other Spaces (Fault line) brings together Portuguese and international artists who explore, through photography, the ways in which human bonds are formed, negotiated and dissolved. Taking the experience of love as one of its guiding threads, the exhibition unfolds as a narrative that moves through desire, intimacy, closeness, tension, distance and loss.

A fault line is a fracture in the Earth''s crust where two tectonic plates meet, building up tension and, as they shift, irreversibly transforming the landscape. The exhibition adopts this image as a metaphor for thinking about human relationships as a terrain of contact and instability, where every act of coming together already contains the possibility of change.','https://macam.pt/en/whats-on/other-spaces','https://cms.macam.pt/storage/uploads/thumbs/yourclosehands_w1920.jpg',0,'2026-11-06','2027-04-12');
CREATE TABLE exhibition_reviews (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	exhibition_id INTEGER NOT NULL, 
	rating INTEGER, 
	review TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_exhibition_review_rating_range CHECK (rating BETWEEN 1 AND 10), 
	FOREIGN KEY(exhibition_id) REFERENCES exhibition (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_exhibition_review UNIQUE (user_id, exhibition_id)
);
INSERT INTO "exhibition_reviews" VALUES(1,2,1,4,'Great collection, go early to avoid the crowds.','2026-10-24 09:53:04.393033','2026-10-24 09:53:04.393036');
CREATE TABLE exhibition_visits (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	exhibition_id INTEGER NOT NULL, 
	visit_date DATE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(exhibition_id) REFERENCES exhibition (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_exhibition_visit UNIQUE (user_id, exhibition_id, visit_date)
);
INSERT INTO "exhibition_visits" VALUES(1,2,1,'2026-05-01');
CREATE TABLE exhibition_wishlist (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	exhibition_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(exhibition_id) REFERENCES exhibition (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_exhibition_wish UNIQUE (user_id, exhibition_id)
);
INSERT INTO "exhibition_wishlist" VALUES(1,2,2);
CREATE TABLE museum (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	country VARCHAR(50) NOT NULL, 
	city VARCHAR(50) NOT NULL, 
	description TEXT, 
	website VARCHAR(254), 
	image_url VARCHAR(254), 
	address VARCHAR(254) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_museum UNIQUE (name, city)
);
INSERT INTO "museum" VALUES(1,'Museu do Aljube – Resistência e Liberdade','Portugal','Lisbon','Situado na antiga prisão do Aljube que, entre 1928 e 1965, funcionou como cárcere político do Estado Novo, tem como missão a preservação da memória do combate à ditadura e daqueles que lutaram pela liberdade e democracia.','https://www.museudoaljube.pt/en/','https://europeanmemories.net/wp-content/uploads/sites/19/2016/09/images.png','R. Augusto Rosa 42, 1100-059 Lisboa','2026-10-24 09:53:04.336701','2026-10-24 09:53:04.336703');
INSERT INTO "museum" VALUES(2,'Museu Nacional dos Coches','Portugal','Lisbon','O Museu Nacional dos Coches reúne uma coleção única no mundo de viaturas de gala e de passeio dos séculos XVI a XIX, na sua maioria provenientes da Casa Real Portuguesa, a que se acrescentaram veículos vindos dos bens da Igreja e de coleções particulares.','https://www.mncoches.gov.pt/en','https://media.timeout.com/images/103703334/750/422/image.jpg','Av. da Índia 136, 1300-300 Lisboa','2026-10-24 09:53:04.337451','2026-10-24 09:53:04.337453');
INSERT INTO "museum" VALUES(3,'Museu do Oriente','Portugal','Lisbon','Inaugurado em 2008 num edifício ímpar na frente ribeirinha de Lisboa, o Museu do Oriente apresenta-se como um museu multicultural que preserva, em todas as suas vertentes, o património material e imaterial de vários países asiáticos, através dos testemunhos das suas duas colecções: Presença Portuguesa na Ásia e Kwok On.

Da presença portuguesa em territórios orientais (Índia, Sri Lanka, China, Macau, Japão e Timor-Leste) resultaram, para além das trocas comerciais, trocas culturais, vivenciais, científicas, técnicas e religiosas que possibilitaram o conhecimento de mundos até então desconhecidos.

A diversidade cultural patente evidencia um diálogo estimulante e enriquecedor entre o Ocidente e o Oriente.','https://www.foriente.pt/home.php','https://upload.wikimedia.org/wikipedia/commons/5/59/Fundacao_oriente.jpg','Av. Brasília, 1350-352 Lisboa','2026-10-24 09:53:04.338002','2026-10-24 09:53:04.338004');
INSERT INTO "museum" VALUES(4,'MACAM','Portugal','Lisbon','The MACAM - Museu de Arte Contemporânea Armando Martins, opens to the world the collection of Portuguese modern art, and national and international contemporary art that the collector Armando Martins began in 1974 and continues to develop.

In addition to the permanent exhibition of the collection, MACAM presents other temporary exhibitions to its visitors and a parallel program of conferences and meetings that promote reflection on the exhibition program.

This museological space embraces an innovative concept: The House of Private Collections. A house where the private becomes public, to receive and present other private collections.','https://macam.pt/en','https://cms.macam.pt/storage/uploads/media/metadata-02.jpg','Rua da Junqueira 66, 1300-343 Lisboa','2026-10-24 09:53:04.338535','2026-10-24 09:53:04.338537');
CREATE TABLE museum_reviews (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	rating INTEGER, 
	review TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_museum_review_rating_range CHECK (rating BETWEEN 1 AND 10), 
	FOREIGN KEY(museum_id) REFERENCES museum (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_museum_review UNIQUE (user_id, museum_id)
);
INSERT INTO "museum_reviews" VALUES(1,2,1,4,'Great collection, go early to avoid the crowds.','2026-10-24 09:53:04.388956','2026-10-24 09:53:04.388958');
CREATE TABLE museum_visits (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	visit_date DATE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(museum_id) REFERENCES museum (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_museum_visit UNIQUE (user_id, museum_id, visit_date)
);
INSERT INTO "museum_visits" VALUES(1,2,1,'2026-05-01');
CREATE TABLE museum_wishlist (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(museum_id) REFERENCES museum (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id), 
	CONSTRAINT uq_user_museum_wish UNIQUE (user_id, museum_id)
);
INSERT INTO "museum_wishlist" VALUES(1,2,2);
CREATE TABLE opening_hours (
	id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	last_entry TIME, 
	is_closed BOOLEAN NOT NULL, 
	is_special BOOLEAN NOT NULL, 
	label VARCHAR(100), 
	notes TEXT, 
	valid_from DATE, 
	valid_to DATE, 
	weekday INTEGER, 
	start_time TIME, 
	end_time TIME, 
	week_of_month INTEGER, 
	month INTEGER, 
	day INTEGER, 
	holidays BOOLEAN NOT NULL, 
	month_from INTEGER, 
	month_to INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_hours_closed_or_times CHECK ((is_closed AND start_time IS NULL AND end_time IS NULL AND last_entry IS NULL) OR (NOT is_closed AND start_time IS NOT NULL AND end_time IS NOT NULL)), 
	CONSTRAINT ck_hours_month_day_pair CHECK ((month IS NULL) = (day IS NULL)), 
	CONSTRAINT ck_hours_month_range CHECK ((month_from IS NULL AND month_to IS NULL) OR (month_from BETWEEN 1 AND 12 AND month_to BETWEEN 1 AND 12 AND month_from <= month_to)), 
	CONSTRAINT ck_hours_holidays_alone CHECK (NOT holidays OR (weekday IS NULL AND month IS NULL AND day IS NULL)), 
	CONSTRAINT ck_hours_day CHECK (day IS NULL OR day BETWEEN 1 AND 31), 
	CONSTRAINT ck_hours_month CHECK (month IS NULL OR month BETWEEN 1 AND 12), 
	CONSTRAINT ck_hours_time_range CHECK (start_time < end_time), 
	CONSTRAINT ck_hours_valid_range CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to), 
	CONSTRAINT ck_hours_week_of_month CHECK (week_of_month IS NULL OR (weekday IS NOT NULL AND (week_of_month = -1 OR week_of_month BETWEEN 1 AND 5))), 
	CONSTRAINT ck_hours_weekday CHECK (weekday IS NULL OR weekday BETWEEN 0 AND 6), 
	FOREIGN KEY(museum_id) REFERENCES museum (id) ON DELETE CASCADE
);
INSERT INTO "opening_hours" VALUES(1,1,NULL,1,0,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(2,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,1,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(3,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,2,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(4,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,3,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(5,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,4,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(6,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,5,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(7,1,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,6,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(8,1,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(9,1,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,5,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(10,1,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,24,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(11,1,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,25,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(12,1,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,12,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(13,2,NULL,1,0,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(14,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,1,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(15,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,2,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(16,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,3,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(17,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,4,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(18,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,5,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(19,2,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,6,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(20,2,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(21,2,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,5,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(22,2,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,6,13,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(23,2,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,25,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(24,3,NULL,1,0,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(25,3,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,1,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(26,3,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,2,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(27,3,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,3,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(28,3,'19:30:00.000000',0,0,NULL,NULL,NULL,NULL,4,'10:00:00.000000','20:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(29,3,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,5,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(30,3,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,6,'10:00:00.000000','18:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(31,3,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(32,3,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,25,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(33,4,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,0,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(34,4,NULL,1,0,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(35,4,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,2,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(36,4,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,3,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(37,4,'19:30:00.000000',0,0,NULL,NULL,NULL,NULL,4,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(38,4,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,5,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(39,4,'17:30:00.000000',0,0,NULL,NULL,NULL,NULL,6,'10:00:00.000000','19:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(40,4,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(41,4,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,5,1,0,NULL,NULL);
INSERT INTO "opening_hours" VALUES(42,4,NULL,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,12,25,0,NULL,NULL);
CREATE TABLE pass_prices (
	id INTEGER NOT NULL, 
	pass_id INTEGER NOT NULL, 
	label VARCHAR(100) NOT NULL, 
	duration_unit VARCHAR(6) NOT NULL, 
	duration_value INTEGER NOT NULL, 
	price NUMERIC(8, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	notes TEXT, 
	resident_country VARCHAR(2), 
	resident_municipality VARCHAR(100), 
	min_age INTEGER, 
	max_age INTEGER, 
	is_student BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT duration_unit CHECK (duration_unit IN ('hours', 'days', 'months', 'years')), 
	CONSTRAINT duration_unit CHECK (duration_unit IN ('hours', 'days', 'months', 'years')), 
	CONSTRAINT ck_pass_price_duration_positive CHECK (duration_value > 0), 
	CONSTRAINT ck_pass_price_age_range CHECK (min_age IS NULL OR max_age IS NULL OR min_age <= max_age), 
	CONSTRAINT ck_pass_price_min_age CHECK (min_age IS NULL OR min_age >= 0), 
	CONSTRAINT ck_pass_price_nonneg CHECK (price >= 0), 
	FOREIGN KEY(pass_id) REFERENCES passes (id) ON DELETE CASCADE, 
	CONSTRAINT uq_pass_price_label UNIQUE (pass_id, label, duration_value, duration_unit), 
	CONSTRAINT duration_unit CHECK (duration_unit IN ('hours', 'days', 'months', 'years'))
);
INSERT INTO "pass_prices" VALUES(1,1,'Adult - 24h','hours',24,31,'EUR',NULL,NULL,NULL,16,NULL,0);
INSERT INTO "pass_prices" VALUES(2,1,'Child - 24h','hours',24,21,'EUR',NULL,NULL,NULL,4,15,0);
INSERT INTO "pass_prices" VALUES(3,1,'Adult - 48h','hours',48,51,'EUR',NULL,NULL,NULL,16,NULL,0);
INSERT INTO "pass_prices" VALUES(4,1,'Child - 48h','hours',48,28,'EUR',NULL,NULL,NULL,4,15,0);
INSERT INTO "pass_prices" VALUES(5,1,'Adult - 72h','hours',72,62,'EUR',NULL,NULL,NULL,16,NULL,0);
INSERT INTO "pass_prices" VALUES(6,1,'Child - 72h','hours',72,35,'EUR',NULL,NULL,NULL,4,15,0);
INSERT INTO "pass_prices" VALUES(7,2,'Adult','days',1,40,'EUR',NULL,NULL,NULL,25,NULL,0);
INSERT INTO "pass_prices" VALUES(8,2,'Young','days',1,20,'EUR',NULL,NULL,NULL,13,24,0);
INSERT INTO "pass_prices" VALUES(9,2,'Senior','days',1,20,'EUR',NULL,NULL,NULL,65,NULL,0);
INSERT INTO "pass_prices" VALUES(10,3,'Adult','days',1,30,'EUR',NULL,NULL,NULL,25,NULL,0);
INSERT INTO "pass_prices" VALUES(11,3,'Young','days',1,15,'EUR',NULL,NULL,NULL,13,24,0);
INSERT INTO "pass_prices" VALUES(12,3,'Senior','days',1,15,'EUR',NULL,NULL,NULL,65,NULL,0);
INSERT INTO "pass_prices" VALUES(13,4,'Adult','days',1,25,'EUR',NULL,NULL,NULL,25,NULL,0);
INSERT INTO "pass_prices" VALUES(14,4,'Young','days',1,12.5,'EUR',NULL,NULL,NULL,13,24,0);
INSERT INTO "pass_prices" VALUES(15,4,'Senior','days',1,12.5,'EUR',NULL,NULL,NULL,65,NULL,0);
CREATE TABLE passes (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	website VARCHAR(254), 
	notes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "passes" VALUES(1,'Lisboa Card','https://www.visitlisboa.com/en/p/lisboa-card','Includes free transportation in lisbon');
INSERT INTO "passes" VALUES(2,'Combinado: Jerónimos, Coches e Ajuda','https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches',NULL);
INSERT INTO "passes" VALUES(3,'Combinado: Jerónimos e Coches','https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches',NULL);
INSERT INTO "passes" VALUES(4,'Combinado: Lisboa real','https://mmp.bymeoblueticket.pt/pt/event/14769/museu-nacional-dos-coches',NULL);
INSERT INTO "passes" VALUES(5,'Acesso 52','https://www.gov.pt/noticias/museus-monumentos-e-palacios-com-entrada-gratis-52-dias-por-ano','Only for Portuguese residents');
CREATE TABLE ticket_exhibition (
	ticket_id INTEGER NOT NULL, 
	exhibition_id INTEGER NOT NULL, 
	PRIMARY KEY (ticket_id, exhibition_id), 
	FOREIGN KEY(exhibition_id) REFERENCES exhibition (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
);
INSERT INTO "ticket_exhibition" VALUES(1,3);
INSERT INTO "ticket_exhibition" VALUES(1,1);
INSERT INTO "ticket_exhibition" VALUES(1,2);
INSERT INTO "ticket_exhibition" VALUES(2,3);
INSERT INTO "ticket_exhibition" VALUES(2,1);
INSERT INTO "ticket_exhibition" VALUES(2,2);
INSERT INTO "ticket_exhibition" VALUES(3,3);
INSERT INTO "ticket_exhibition" VALUES(3,1);
INSERT INTO "ticket_exhibition" VALUES(3,2);
INSERT INTO "ticket_exhibition" VALUES(4,3);
INSERT INTO "ticket_exhibition" VALUES(4,1);
INSERT INTO "ticket_exhibition" VALUES(4,2);
INSERT INTO "ticket_exhibition" VALUES(5,3);
INSERT INTO "ticket_exhibition" VALUES(5,1);
INSERT INTO "ticket_exhibition" VALUES(5,2);
INSERT INTO "ticket_exhibition" VALUES(6,3);
INSERT INTO "ticket_exhibition" VALUES(6,1);
INSERT INTO "ticket_exhibition" VALUES(6,2);
INSERT INTO "ticket_exhibition" VALUES(7,3);
INSERT INTO "ticket_exhibition" VALUES(7,1);
INSERT INTO "ticket_exhibition" VALUES(7,2);
INSERT INTO "ticket_exhibition" VALUES(12,4);
INSERT INTO "ticket_exhibition" VALUES(12,6);
INSERT INTO "ticket_exhibition" VALUES(12,5);
INSERT INTO "ticket_exhibition" VALUES(13,4);
INSERT INTO "ticket_exhibition" VALUES(13,6);
INSERT INTO "ticket_exhibition" VALUES(13,5);
INSERT INTO "ticket_exhibition" VALUES(14,4);
INSERT INTO "ticket_exhibition" VALUES(14,6);
INSERT INTO "ticket_exhibition" VALUES(14,5);
INSERT INTO "ticket_exhibition" VALUES(15,4);
INSERT INTO "ticket_exhibition" VALUES(15,6);
INSERT INTO "ticket_exhibition" VALUES(15,5);
INSERT INTO "ticket_exhibition" VALUES(20,6);
INSERT INTO "ticket_exhibition" VALUES(20,5);
INSERT INTO "ticket_exhibition" VALUES(20,4);
INSERT INTO "ticket_exhibition" VALUES(16,4);
INSERT INTO "ticket_exhibition" VALUES(16,6);
INSERT INTO "ticket_exhibition" VALUES(16,5);
INSERT INTO "ticket_exhibition" VALUES(17,4);
INSERT INTO "ticket_exhibition" VALUES(17,6);
INSERT INTO "ticket_exhibition" VALUES(17,5);
INSERT INTO "ticket_exhibition" VALUES(18,4);
INSERT INTO "ticket_exhibition" VALUES(18,6);
INSERT INTO "ticket_exhibition" VALUES(18,5);
INSERT INTO "ticket_exhibition" VALUES(19,4);
INSERT INTO "ticket_exhibition" VALUES(19,6);
INSERT INTO "ticket_exhibition" VALUES(19,5);
INSERT INTO "ticket_exhibition" VALUES(21,8);
INSERT INTO "ticket_exhibition" VALUES(21,9);
INSERT INTO "ticket_exhibition" VALUES(21,7);
INSERT INTO "ticket_exhibition" VALUES(21,10);
INSERT INTO "ticket_exhibition" VALUES(22,8);
INSERT INTO "ticket_exhibition" VALUES(22,9);
INSERT INTO "ticket_exhibition" VALUES(22,7);
INSERT INTO "ticket_exhibition" VALUES(22,10);
INSERT INTO "ticket_exhibition" VALUES(23,8);
INSERT INTO "ticket_exhibition" VALUES(23,9);
INSERT INTO "ticket_exhibition" VALUES(23,7);
INSERT INTO "ticket_exhibition" VALUES(23,10);
INSERT INTO "ticket_exhibition" VALUES(24,8);
INSERT INTO "ticket_exhibition" VALUES(24,9);
INSERT INTO "ticket_exhibition" VALUES(24,7);
INSERT INTO "ticket_exhibition" VALUES(24,10);
INSERT INTO "ticket_exhibition" VALUES(25,8);
INSERT INTO "ticket_exhibition" VALUES(25,9);
INSERT INTO "ticket_exhibition" VALUES(25,7);
INSERT INTO "ticket_exhibition" VALUES(25,10);
INSERT INTO "ticket_exhibition" VALUES(28,11);
INSERT INTO "ticket_exhibition" VALUES(28,12);
INSERT INTO "ticket_exhibition" VALUES(28,13);
INSERT INTO "ticket_exhibition" VALUES(29,11);
INSERT INTO "ticket_exhibition" VALUES(30,12);
INSERT INTO "ticket_exhibition" VALUES(30,13);
INSERT INTO "ticket_exhibition" VALUES(31,12);
INSERT INTO "ticket_exhibition" VALUES(31,13);
INSERT INTO "ticket_exhibition" VALUES(32,12);
INSERT INTO "ticket_exhibition" VALUES(32,13);
INSERT INTO "ticket_exhibition" VALUES(32,11);
INSERT INTO "ticket_exhibition" VALUES(33,11);
INSERT INTO "ticket_exhibition" VALUES(34,12);
INSERT INTO "ticket_exhibition" VALUES(34,13);
INSERT INTO "ticket_exhibition" VALUES(35,12);
INSERT INTO "ticket_exhibition" VALUES(35,13);
INSERT INTO "ticket_exhibition" VALUES(36,12);
INSERT INTO "ticket_exhibition" VALUES(36,13);
INSERT INTO "ticket_exhibition" VALUES(36,11);
INSERT INTO "ticket_exhibition" VALUES(37,11);
INSERT INTO "ticket_exhibition" VALUES(38,12);
INSERT INTO "ticket_exhibition" VALUES(38,13);
INSERT INTO "ticket_exhibition" VALUES(39,12);
INSERT INTO "ticket_exhibition" VALUES(39,13);
INSERT INTO "ticket_exhibition" VALUES(40,12);
INSERT INTO "ticket_exhibition" VALUES(40,11);
INSERT INTO "ticket_exhibition" VALUES(40,13);
INSERT INTO "ticket_exhibition" VALUES(41,11);
INSERT INTO "ticket_exhibition" VALUES(42,12);
INSERT INTO "ticket_exhibition" VALUES(42,13);
INSERT INTO "ticket_exhibition" VALUES(43,12);
INSERT INTO "ticket_exhibition" VALUES(43,13);
INSERT INTO "ticket_exhibition" VALUES(44,12);
INSERT INTO "ticket_exhibition" VALUES(44,11);
INSERT INTO "ticket_exhibition" VALUES(44,13);
INSERT INTO "ticket_exhibition" VALUES(45,11);
INSERT INTO "ticket_exhibition" VALUES(46,12);
INSERT INTO "ticket_exhibition" VALUES(46,13);
INSERT INTO "ticket_exhibition" VALUES(47,12);
INSERT INTO "ticket_exhibition" VALUES(47,13);
INSERT INTO "ticket_exhibition" VALUES(48,12);
INSERT INTO "ticket_exhibition" VALUES(48,13);
INSERT INTO "ticket_exhibition" VALUES(48,11);
INSERT INTO "ticket_exhibition" VALUES(49,12);
INSERT INTO "ticket_exhibition" VALUES(49,13);
INSERT INTO "ticket_exhibition" VALUES(49,11);
CREATE TABLE tickets (
	id INTEGER NOT NULL, 
	museum_id INTEGER NOT NULL, 
	label VARCHAR(100) NOT NULL, 
	price NUMERIC(8, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	notes TEXT, 
	pass_id INTEGER, 
	resident_country VARCHAR(2), 
	resident_municipality VARCHAR(100), 
	min_age INTEGER, 
	max_age INTEGER, 
	is_student BOOLEAN NOT NULL, 
	weekday INTEGER, 
	start_time TIME, 
	end_time TIME, 
	week_of_month INTEGER, 
	month INTEGER, 
	day INTEGER, 
	holidays BOOLEAN NOT NULL, 
	month_from INTEGER, 
	month_to INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_ticket_schedule_kind CHECK ((weekday IS NULL AND month IS NULL AND day IS NULL AND NOT holidays) OR (weekday IS NOT NULL AND month IS NULL AND day IS NULL AND NOT holidays) OR (weekday IS NULL AND month IS NOT NULL AND day IS NOT NULL AND NOT holidays) OR (weekday IS NULL AND month IS NULL AND day IS NULL AND holidays)), 
	CONSTRAINT ck_free_rule_day CHECK (day IS NULL OR day BETWEEN 1 AND 31), 
	CONSTRAINT ck_ticket_age_range CHECK (min_age IS NULL OR max_age IS NULL OR min_age <= max_age), 
	CONSTRAINT ck_ticket_min_age CHECK (min_age IS NULL OR min_age >= 0), 
	CONSTRAINT ck_free_rule_month CHECK (month IS NULL OR month BETWEEN 1 AND 12), 
	CONSTRAINT ck_ticket_price_nonneg CHECK (price >= 0), 
	CONSTRAINT ck_ticket_time_range CHECK (start_time IS NULL OR end_time IS NULL OR start_time < end_time), 
	CONSTRAINT ck_ticket_week_of_month CHECK (week_of_month IS NULL OR (weekday IS NOT NULL AND (week_of_month = -1 OR week_of_month BETWEEN 1 AND 5))), 
	CONSTRAINT ck_free_rule_weekday CHECK (weekday IS NULL OR weekday BETWEEN 0 AND 6), 
	FOREIGN KEY(museum_id) REFERENCES museum (id), 
	FOREIGN KEY(pass_id) REFERENCES passes (id) ON DELETE RESTRICT, 
	CONSTRAINT uq_ticket_museum_label UNIQUE (museum_id, label)
);
INSERT INTO "tickets" VALUES(1,1,'Standard',4,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(2,1,'Senior',2.8,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(3,1,'Young',2,'EUR',NULL,NULL,NULL,NULL,13,25,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(4,1,'Child',0,'EUR',NULL,NULL,NULL,NULL,NULL,12,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(5,1,'Young resident in municipality',0,'EUR',NULL,NULL,NULL,'Lisbon',13,23,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(6,1,'Senior resident in municipality',0,'EUR',NULL,NULL,NULL,'Lisbon',65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(7,1,'Lisboa Card',0,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(8,1,'Sundays',0,'EUR',NULL,NULL,NULL,'Lisbon',NULL,NULL,0,6,NULL,'14:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(9,1,'Holidays',0,'EUR',NULL,NULL,NULL,'Lisbon',NULL,NULL,0,NULL,NULL,'14:00:00.000000',NULL,NULL,NULL,1,NULL,NULL);
INSERT INTO "tickets" VALUES(10,1,'Museum day',0,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,5,18,0,NULL,NULL);
INSERT INTO "tickets" VALUES(11,1,'April 25th',0,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,4,25,0,NULL,NULL);
INSERT INTO "tickets" VALUES(12,2,'Adult',15,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(13,2,'Child',0,'EUR',NULL,NULL,NULL,NULL,NULL,12,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(14,2,'Young',7.5,'EUR',NULL,NULL,NULL,NULL,13,24,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(15,2,'Senior',7.5,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(16,2,'Lisboa Card',0,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(17,2,'Combinado: Jerónimos, Coches e Ajuda',0,'EUR',NULL,2,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(18,2,'Combinado: Jerónimos e Coches',0,'EUR',NULL,3,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(19,2,'Combinado: Lisboa real',0,'EUR',NULL,4,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(20,2,'Acesso 52',0,'EUR',NULL,NULL,'PT',NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(21,3,'Standard',10,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(22,3,'Child',3,'EUR',NULL,NULL,NULL,NULL,6,12,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(23,3,'Student',3.5,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(24,3,'Senior',4.5,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(25,3,'Lisboa Card',8,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(26,3,'Baby',0,'EUR',NULL,NULL,NULL,NULL,NULL,5,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(27,3,'Friday evenings',0,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,4,'18:00:00.000000','20:00:00.000000',NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(28,4,'General Entry',15,'EUR','All exhibitions',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(29,4,'Permanent Exhibition',8,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(30,4,'Temporary Exhibition',6,'EUR','For only 1 temporary exhibition',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(31,4,'Pack - Temporary Exhibitions',10,'EUR','All temporary exhibitions',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(32,4,'General Entry Young',7.5,'EUR',NULL,NULL,NULL,NULL,13,18,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(33,4,'Permanent Exhibition Young',4,'EUR',NULL,NULL,NULL,NULL,13,18,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(34,4,'Temporary Exhibition Young',3,'EUR',NULL,NULL,NULL,NULL,13,18,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(35,4,'Pack - Temporary Exhibitions Young',5,'EUR',NULL,NULL,NULL,NULL,13,18,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(36,4,'General Entry Student',7.5,'EUR',NULL,NULL,NULL,NULL,NULL,25,1,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(37,4,'Permanent Exhibition Student',4,'EUR',NULL,NULL,NULL,NULL,NULL,25,1,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(38,4,'Temporary Exhibition Student',3,'EUR',NULL,NULL,NULL,NULL,NULL,25,1,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(39,4,'Pack - Temporary Exhibitions Student',5,'EUR',NULL,NULL,NULL,NULL,NULL,25,1,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(40,4,'General Entry Senior',7.5,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(41,4,'Permanent Exhibition Senior',4,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(42,4,'Temporary Exhibition Senior',3,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(43,4,'Pack - Temporary Exhibitions Senior',5,'EUR',NULL,NULL,NULL,NULL,65,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(44,4,'General Entry Lisboa Card',13.5,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(45,4,'Permanent Exhibition Lisboa Card',7.2,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(46,4,'Temporary Exhibition Lisboa Card',5.4,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(47,4,'Pack - Temporary Exhibitions Lisboa Card',9,'EUR',NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(48,4,'First Monday of the month',0,'EUR',NULL,NULL,NULL,NULL,NULL,NULL,0,0,'10:00:00.000000','14:00:00.000000',1,NULL,NULL,0,NULL,NULL);
INSERT INTO "tickets" VALUES(49,4,'Child',0,'EUR',NULL,NULL,NULL,NULL,NULL,12,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL);
CREATE TABLE user_account (
	id INTEGER NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (username)
);
INSERT INTO "user_account" VALUES(1,'admin','admin','admin','admin@example.com','scrypt:32768:8:1$EQTsN42vmzVDbscj$6045e19057ad9b301b27fa239f0f2e307e5a56a166b5437a5801553800a667bcfee91a60fa7ef80f0aefd5e435b9429d623d2804490dd9315e6f978be48c5a1b',1,'2026-10-24 09:53:04.230031');
INSERT INTO "user_account" VALUES(2,'alice','Alice','Ficticio','alice@example.com','scrypt:32768:8:1$By0ydkeeRwKSRHcu$58b21daf0d5d34d8bcfb994062c49bab81807ddd648e096dd0c207610a2a6d30ae16c2e2017e1613283710c072b7c50dd7b8b953b9361e82906dde447d4bf49a',0,'2026-10-24 09:53:04.334023');
COMMIT;
