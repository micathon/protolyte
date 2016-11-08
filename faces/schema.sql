drop table if exists dirs;
drop table if exists images;
drop table if exists tags;
drop table if exists tagmast;
drop table if exists tagdetl;
create table dirs (
  dirid integer primary key autoincrement,
  parid integer,
  dirname text not null,
  firstid integer,
  emptyid integer,
  isdel bool
);
create table images (
  imgid integer primary key autoincrement,
  dirid integer,
  filename text not null,
  nextid integer,
  isurl bool,
  isvid bool,
  isdel bool
);
create table tags (
  id integer primary key autoincrement,
  imgid integer,
  tagid integer,
  desc text not null,
  isdel bool
);
create table tagmast (
  tagid integer primary key autoincrement,
  tagname text not null,
  isdel bool
);

