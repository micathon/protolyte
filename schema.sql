drop table if exists imgtab;
drop table if exists picrotab;
drop table if exists rowtab;
drop table if exists tapetab;
drop table if exists bytrotab;
create table imgtab (
  id integer primary key autoincrement,
  proid integer,
  filename text not null,
  iscore bool
);
create table picrotab (
  id integer primary key autoincrement,
  bytid integer,
  picroname text not null
);
create table bytrotab (
  id integer primary key autoincrement,
  bytroname text not null
);

