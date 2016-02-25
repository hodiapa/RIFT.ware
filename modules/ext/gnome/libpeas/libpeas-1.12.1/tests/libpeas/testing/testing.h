/*
 * testing.h
 * This file is part of libpeas
 *
 * Copyright (C) 2010 - Garrett Regier
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU Library General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU Library General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#ifndef __TESTING_H__
#define __TESTING_H__

#include <libpeas/peas-engine.h>
#include <testing-util.h>

G_BEGIN_DECLS

void        testing_init             (gint    *argc,
                                      gchar ***argv);

PeasEngine *testing_engine_new_full  (gboolean nonglobal_loaders);

#define testing_engine_new() (testing_engine_new_full (FALSE))

/* libtesting-util functions which do not need to be overridden */
#define testing_engine_free testing_util_engine_free
#define testing_run_tests   testing_util_run_tests

G_END_DECLS

#endif /* __TESTING_H__ */