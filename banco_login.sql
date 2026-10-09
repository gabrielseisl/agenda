-- Rode no MySQL Workbench / phpMyAdmin.
-- ATENÇÃO: apaga as atividades de teste que já existem (a tabela ganha a coluna usuario_id).
USE agenda;

CREATE TABLE IF NOT EXISTS usuarios (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  nome       VARCHAR(100) NOT NULL,
  email      VARCHAR(150) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY ix_usuarios_email (email)
);

DROP TABLE IF EXISTS atividades;

CREATE TABLE atividades (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id  INT NOT NULL,
  titulo      VARCHAR(150) NOT NULL,
  `data`      DATE NOT NULL,
  horario     TIME NULL,
  duracao_min INT NOT NULL DEFAULT 30,
  prioridade  VARCHAR(10) NOT NULL DEFAULT 'media',
  concluida   TINYINT(1) NOT NULL DEFAULT 0,
  criado_em   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_atividades_usuario_id (usuario_id),
  INDEX ix_atividades_data (`data`),
  CONSTRAINT fk_atividades_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuarios (id) ON DELETE CASCADE
);
