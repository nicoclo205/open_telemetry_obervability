CREATE TABLE IF NOT EXISTS stickers (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    pais          VARCHAR(50)  NOT NULL,
    numero        INTEGER      NOT NULL,
    rareza        VARCHAR(20)  CHECK (rareza IN ('comun', 'raro', 'legendario')),
    coleccionado  BOOLEAN      DEFAULT FALSE,
    numero_album  INTEGER      NOT NULL
);

INSERT INTO stickers (nombre, pais, numero, rareza, coleccionado, numero_album) VALUES
-- Álbum 1 (Qatar 2022)
('Lionel Messi',        'Argentina',   10, 'legendario', TRUE,  1),
('Ángel Di María',      'Argentina',   11, 'raro',       TRUE,  1),
('Neymar Jr',           'Brasil',      10, 'legendario', FALSE, 1),
('Vinicius Jr',         'Brasil',      11, 'raro',       TRUE,  1),
('Kylian Mbappé',       'Francia',     10, 'legendario', TRUE,  1),
('Antoine Griezmann',   'Francia',     11, 'raro',       FALSE, 1),
('Harry Kane',          'Inglaterra',  9,  'raro',       TRUE,  1),
('Bukayo Saka',         'Inglaterra',  7,  'comun',      FALSE, 1),
('Pedri',               'España',      8,  'raro',       TRUE,  1),
('Gavi',                'España',      6,  'comun',      TRUE,  1),
('Luka Modric',         'Croacia',     10, 'legendario', FALSE, 1),
('Achraf Hakimi',       'Marruecos',   2,  'raro',       TRUE,  1),

-- Álbum 2 (Rusia 2018)
('Cristiano Ronaldo',   'Portugal',    7,  'legendario', TRUE,  2),
('Bruno Fernandes',     'Portugal',    8,  'raro',       FALSE, 2),
('Romelu Lukaku',       'Bélgica',     9,  'raro',       TRUE,  2),
('Kevin De Bruyne',     'Bélgica',     7,  'legendario', TRUE,  2),
('Thomas Müller',       'Alemania',    13, 'raro',       FALSE, 2),
('Manuel Neuer',        'Alemania',    1,  'raro',       TRUE,  2),
('Robert Lewandowski',  'Polonia',     9,  'legendario', FALSE, 2),
('Hirving Lozano',      'México',      22, 'comun',      TRUE,  2),
('Carlos Vela',         'México',      17, 'raro',       FALSE, 2),
('Luis Suárez',         'Uruguay',     9,  'raro',       TRUE,  2),
('Edinson Cavani',      'Uruguay',     21, 'comun',      FALSE, 2),
('James Rodríguez',     'Colombia',    10, 'legendario', TRUE,  2),

-- Álbum 3 (Brasil 2014)
('Arjen Robben',        'Países Bajos',11, 'raro',       TRUE,  3),
('Xavi Hernández',      'España',      8,  'legendario', FALSE, 3),
('Andrés Iniesta',      'España',      6,  'legendario', TRUE,  3),
('Son Heung-min',       'Corea del Sur',7, 'raro',       FALSE, 3),
('Keylor Navas',        'Costa Rica',  1,  'comun',      TRUE,  3),
('Clint Dempsey',       'Estados Unidos',8,'comun',      FALSE, 3),
('Sadio Mané',          'Senegal',     10, 'raro',       TRUE,  3),
('Riyad Mahrez',        'Argelia',     26, 'comun',      FALSE, 3),
('Tim Cahill',          'Australia',   4,  'comun',      TRUE,  3),
('Xherdan Shaqiri',     'Suiza',       23, 'comun',      FALSE, 3);
