import sys
import argparse
import functools
import os
import re
from types import SimpleNamespace

import arrow
import yaml
# from colorist import Color, Effect

from lib.data import PTOFile
from lib.ui import Table


# class ACTUALLY_NONE:
#     pass


# def _arg_date(val):
#     return arrow.get(val).replace(hour=0, minute=0, second=0, microsecond=0)


# def _arg_maybe_bool(val):
#     val = str(val).strip().lower()
#     return val and val[0] in ['t', 'y', '1']

# def _arg_maybe_bool_or_none(val):
#     val = str(val).strip().lower()
#     if val[0] in ['-', 'x']:
#         return ACTUALLY_NONE
#     return _arg_maybe_bool(val)


# def _arg_duration(val):
#     if val:
#         val = str(val)
#         mul = 1.0
#         if val.endswith('d'):
#             mul = 8.0
#             val = val[:-1]
#         val = float(val) * mul
#     return val


# def _has_collection(callback):
#     @functools.wraps(callback)
#     def _has_collection_wrap(args, *a, **ka):
#         colls = storage.load()
#         if args.collection:
#             by_fname = {o.filename: o for o in colls}
#             coll = by_fname[args.collection]
#         else:
#             coll = colls[-1]
#         return callback(args, coll, *a, **ka)
#     return _has_collection_wrap


# def _has_type(arg, optional=False):
#     def _has_type_impl(callback):
#         @functools.wraps(callback)
#         def _has_type_wrap(args, coll, *a, **ka):
#             by_key = {t.key: t for t in coll.pto_types}
#             if optional:
#                 type_ = by_key.get(getattr(args, arg))
#             else:
#                 type_ = by_key[getattr(args, arg)]
#             return callback(args, coll, type_, *a, **ka)
#         return _has_type_wrap
#     return _has_type_impl


# def _has_entry(arg, optional=False):
#     def _has_entry_impl(callback):
#         @functools.wraps(callback)
#         def _has_entry_wrap(args, coll, *a, **ka):
#             entry = coll.entries[getattr(args, arg) - 1]
#             return callback(args, coll, entry, *a, **ka)
#         return _has_entry_wrap
#     return _has_entry_impl


# def cmd_list_files(args):
#     rows = [[c.filename, c.start.format('YYYY-MM-DD')] for c in storage.load()]
#     print(tabulate(rows, headers=['Filename', 'Starts']))


# def cmd_new_file(args):
#     coll = data.PTOCollection(start=args.start)
#     storage.save(coll)
#     print(f"Saved new PTO collection to {coll.filename}")


# @_has_collection
# def cmd_add_type(args, coll):
#     kw = dict(
#         key=args.key,
#         name=args.name,
#         short=args.short_name,
#         order=args.order,
#         init_balance=args.balance,
#         resolution=args.resolution,
#         accrued=args.accrued,
#     )
#     if args.accrued:
#         if args.accrual_days is not None:
#             kw['accrual_days'] = args.accrual_days
#         if args.accrual_amount is not None:
#             kw['accrual_amount'] = args.accrual_amount
#         if args.accrual_total is not None:
#             kw['accrual_total'] = args.accrual_total
#     type_ = data.PTOType(**kw)
#     coll.pto_types.append(type_)
#     storage.save(coll)
#     print(f"Added new PTO type {type_.name} ({type_.key}) to collection {coll.filename}")


# @_has_collection
# @_has_type('key')
# def cmd_edit_type(args, coll, type_):
#     if args.name is not None:
#         type_.name = args.name

#     if args.short_name is not None:
#         type_.short = args.short_name

#     if args.name is not None:
#         type_.name = args.name

#     if args.order is not None:
#         type_.order = args.order

#     if args.balance is not None:
#         type_.init_balance = args.balance

#     if args.resolution is not None:
#         type_.resolution = args.resolution

#     if args.accrued is not None:
#         type_.accrued = args.accrued

#     if args.accrual_days is not None:
#         type_.accrual_days = args.accrual_days

#     if args.accrual_amount is not None:
#         type_.accrual_amount = args.accrual_amount

#     if args.accrual_total is not None:
#         type_.accrual_total = args.accrual_total

#     storage.save(coll)
#     print(f"Saved PTO type {type_.name} ({type_.key}) to collection {coll.filename}")


# @_has_collection
# @_has_type('type')
# def cmd_add_entry(args, coll, type_):
#     end = None
#     if args.end:
#         end = args.end
#     elif args.duration:
#         end = args.date.shift(hours=int(args.duration * 24.0))
#     kw = dict(
#         name=args.name,
#         pto_type=type_.key,
#         date=args.date,
#         amount=args.amount,
#         end=end,
#         tentative=args.tentative,
#         requested=args.requested,
#         approved=args.approved,
#         travel=args.travel,
#         lodging=args.lodging,
#         registration=args.registration,
#         roommates=args.roommates,
#     )
#     ent = data.PTOEntry(**kw)
#     coll.entries.append(ent)
#     storage.save(coll)
#     print(f"Added entry {ent.name} ({type_.name}) to collection {coll.filename}")


# @_has_collection
# @_has_type('type', optional=True)
# @_has_entry('id')
# def cmd_edit_entry(args, coll, entry, type_):
#     if type_ is not None:
#         entry.pto_type = type_.key

#     if args.name is not None:
#         entry.name = args.name

#     if args.date is not None:
#         entry.date = args.date

#     if args.amount is not None:
#         entry.amount = args.amount

#     end = None
#     if args.end:
#         end = args.end
#     elif args.duration:
#         end = entry.date.shift(hours=int(args.duration * 24.0))

#     if end is not None:
#         entry.end = end

#     if args.tentative is not None:
#         entry.tentative = args.tentative

#     if args.requested is not None:
#         entry.requested = args.requested

#     if args.approved is not None:
#         entry.approved = args.approved

#     if args.travel is not ACTUALLY_NONE:
#         entry.travel = args.travel

#     if args.lodging is not ACTUALLY_NONE:
#         entry.lodging = args.lodging

#     if args.registration is not ACTUALLY_NONE:
#         entry.registration = args.registration

#     if args.roommates is not ACTUALLY_NONE:
#         entry.roommates = args.roommates

#     storage.save(coll)
#     print(f"Updated entry {entry.name} in collection {coll.filename}")


# @_has_collection
# def cmd_list_entries(args, coll):
#     entries = [(True, m.model_copy()) for m in coll.entries]
#     types = {m.key: m for m in coll.pto_types}
#     bal_tentative = {m.key: 0.0 for m in coll.pto_types}
#     bal_planned = {m.key: 0.0 for m in coll.pto_types}
#     bal_requested = {m.key: 0.0 for m in coll.pto_types}
#     bal_approved = {m.key: 0.0 for m in coll.pto_types}
#     for t in coll.pto_types:
#         if t.init_balance:
#             entries.append((False, data.PTOEntry(
#                 name='Initial Balance',
#                 pto_type=t.key,
#                 date=coll.start.shift(days=-1),
#                 amount=t.init_balance,
#             )))
#         if t.accrued:
#             # add an accrual entry per accrual day as well as one for any initial balance
#             for m in range(1, 13):
#                 for d in t.accrual_days:
#                     try:
#                         ts = coll.start.replace(month=m, day=d)
#                     except ValueError:
#                         # day out of range; use last day
#                         ts = coll.start
#                         if m == 12:
#                             ts = ts.shift(years=1).replace(month=1, day=1).shift(days=-1)
#                         else:
#                             ts = ts.replace(month=m + 1, day=1).shift(days=-1)
#                     entries.append((False, data.PTOEntry(
#                         name='Accrual',
#                         pto_type=t.key,
#                         date=ts,
#                         amount=t.accrual_amount or t.accrual_total / (12 * len(t.accrual_days)),
#                     )))
#     entries = list(sorted(entries, key=lambda e: e[1].date))
#     headers = ['ID', 'Name', 'Date', 'Status']
#     for pto_type in types.values():
#         for h in ('Tentative', 'Planned', 'Requested', 'Approved'):
#             headers.append(h + ' - ' + pto_type.short_name)
#     headers += ['Travel?', 'Lodging?', 'Registration?', 'Roommates?']
#     # TODO: make this optional
#     header_short_map = {
#         'Tentative': 'Tn',
#         'Planned': 'Pl',
#         'Requested': 'Rq',
#         'Approved': 'Ap',
#         'Travel': 'Tr',
#         'Lodging': 'Lo',
#         'Registration': 'Re',
#         'Roommates': 'Rm',
#     }
#     for i, v in enumerate(list(headers)):
#         for k, e in header_short_map.items():
#             if k in v:
#                 v = v.replace(k, e)
#                 headers[i] = v

#     rows = []
#     def f_maybe_bool(value):
#         if value is None:
#             return Effect.DIM + Color.WHITE + 'NA' + Color.OFF + Effect.DIM_OFF
#         elif value:
#             return Color.GREEN + 'Y' + Color.OFF
#         return Color.RED + 'N' + Color.OFF

#     def f_days(hours):
#         return '{:1.2f}'.format(hours / 8.0)

#     def f_color_num(n, tgood=3, tok=1):
#         if float(n) >= tgood:
#             return Color.GREEN + n + Color.OFF
#         elif float(n) >= tok:
#             return Color.YELLOW + n + Color.OFF
#         return Color.RED + n + Color.OFF

#     def f_status(entry):
#         if entry.approved:
#             return Color.GREEN + 'Approved' + Color.OFF
#         elif entry.requested:
#             return Color.YELLOW + 'Requested' + Color.OFF
#         elif entry.tentative:
#             return Effect.DIM + Color.WHITE + 'Tentative' + Color.OFF + Effect.DIM_OFF
#         else:
#             return Color.RED + 'Planned' + Color.OFF

#     def f_for_status(entry, text):
#         if entry.tentative:
#             return Effect.DIM + Color.WHITE + text + Color.OFF + Effect.DIM_OFF
#         elif entry.approved and all((v is None or v is True for v in (entry.travel, entry.lodging, entry.registration, entry.roommates))):
#             return Color.GREEN + text + Color.OFF
#         return Color.RED + text + Color.OFF

#     for is_pto, entry in entries:
#         if is_pto:
#             if entry.approved:
#                 bal_approved[entry.pto_type] -= entry.amount
#                 bal_requested[entry.pto_type] -= entry.amount
#                 bal_planned[entry.pto_type] -= entry.amount
#                 bal_tentative[entry.pto_type] -= entry.amount
#             elif entry.requested:
#                 bal_requested[entry.pto_type] -= entry.amount
#                 bal_planned[entry.pto_type] -= entry.amount
#                 bal_tentative[entry.pto_type] -= entry.amount
#             elif entry.tentative:
#                 bal_tentative[entry.pto_type] -= entry.amount
#             else:
#                 bal_planned[entry.pto_type] -= entry.amount
#                 bal_tentative[entry.pto_type] -= entry.amount
#             row = [
#                 entry._id,
#                 f_for_status(entry, entry.name),
#                 entry.date.format('YYYY-MM-DD'),
#                 f_status(entry),
#             ]
#             for pto_type in types.values():
#                 if pto_type.key == entry.pto_type:
#                     row += [
#                         f_color_num(f_days(bal_tentative[entry.pto_type])),
#                         f_color_num(f_days(bal_planned[entry.pto_type])),
#                         f_color_num(f_days(bal_requested[entry.pto_type])),
#                         f_color_num(f_days(bal_approved[entry.pto_type])),
#                     ]
#                 else:
#                     row += ['', '', '', '']
#             row += [
#                 f_maybe_bool(entry.travel),
#                 f_maybe_bool(entry.lodging),
#                 f_maybe_bool(entry.registration),
#                 f_maybe_bool(entry.roommates),
#             ]
#             rows.append(row)
#         else:
#             bal_approved[entry.pto_type] += entry.amount
#             bal_requested[entry.pto_type] += entry.amount
#             bal_planned[entry.pto_type] += entry.amount
#             bal_tentative[entry.pto_type] += entry.amount
#             row = [
#                 '',
#                 Effect.DIM + Color.WHITE + types[entry.pto_type].short_name + Color.OFF + Effect.DIM_OFF,
#                 entry.date.format('YYYY-MM-DD'),
#                 Effect.DIM + Color.WHITE + '+' + Color.OFF + Effect.DIM_OFF,
#             ]
#             for pto_type in types.values():
#                 if pto_type.key == entry.pto_type:
#                     row += [
#                         f_color_num(f_days(bal_tentative[entry.pto_type])),
#                         f_color_num(f_days(bal_planned[entry.pto_type])),
#                         f_color_num(f_days(bal_requested[entry.pto_type])),
#                         f_color_num(f_days(bal_approved[entry.pto_type])),
#                     ]
#                 else:
#                     row += ['', '', '', '']
#             row += [
#                 '',
#                 '',
#                 '',
#                 '',
#             ]
#             rows.append(row)
#     print(tabulate(rows, headers=headers))


def load_file(args):
    path = args.file
    if not path:
        candidates = [
            os.path.join('.', 'pto.yaml'),
            os.path.expanduser(os.path.join('~', 'pto.yaml')),
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break
    if not path:
        raise RuntimeError("No pto.yaml found")
    if not os.path.exists(path):
        raise RuntimeError(f"File {path} does not exist")

    with open(path, 'r') as fp:
        data = yaml.load(fp, Loader=yaml.SafeLoader)

    return PTOFile.model_validate(data, context={})


def load_year(args, data):
    years = [c for c in data.collections if c.year == args.year]
    if args.filter:
        years = [c for c in years if args.filter in c.name]

    if years:
        if len(years) > 1:
            raise RuntimeError("Ambiguous entries for year {} ({})".format(args.year, ', '.join((c.name for c in years))))
        return years[0]
    raise RuntimeError("No entries for year {} (found {})".format(args.year, ', '.join((str(c.year) for c in data.collections))))


def list_years(args, data):
    print(Table(
        args,
        data.collections,
        {
            'year': 'Year',
            'name': 'Name',
        }
    ))


def list_pto(args, data):
    def _slug(v):
        return re.sub(r'[^A-Za-z0-9]+', '_', v)

    items = []
    running_balance = {
        _slug(t.short_name): {
            'planned': 0,
            'tentative': 0,
            'requested': 0,
            'approved': 0,
        }
        for t in data.pto_types.values()
    }
    for row in sorted(data.adjustments, key=lambda i: i.date):
        type_ = _slug(row.pto_type.short_name)
        props = {'state': None}
        if row.pto:
            if row.pto.approved is not None:
                props['state'] = 'Denied'
                if row.pto.approved:
                    props['state'] = 'Approved'
                    running_balance[type_]['planned'] += row.hours
                    running_balance[type_]['approved'] += row.hours
                    running_balance[type_]['requested'] += row.hours
                    running_balance[type_]['tentative'] += row.hours
            elif row.pto.requested:
                props['state'] = 'Requested'
                running_balance[type_]['planned'] += row.hours
                running_balance[type_]['tentative'] += row.hours
                running_balance[type_]['requested'] += row.hours
            elif row.pto.tentative:
                props['state'] = 'Tentative'
                running_balance[type_]['tentative'] += row.hours
            else:
                props['state'] = 'Planned'
                running_balance[type_]['tentative'] += row.hours
                running_balance[type_]['planned'] += row.hours
        else:
            running_balance[type_]['planned'] += row.hours
            running_balance[type_]['approved'] += row.hours
            running_balance[type_]['requested'] += row.hours
            running_balance[type_]['tentative'] += row.hours

        props.update({
            'name': row.pto.name if row.pto else None,
            'start': row.pto.start if row.pto else row.date,
            'end': row.pto.end if row.pto else None,
            'type': row.pto_type.short_name,
            'days': None,
            'travel': None,
            'lodging': None,
            'registration': None,
            'roommates': None,
        })
        for t, b in running_balance.items():
            for k, v in b.items():
                props[f'{t}_{k}'] = v
        if row.pto:
            props['days'] = row.pto.days
            for k in ('travel', 'lodging', 'registration', 'roommates'):
                v = getattr(row.pto, k, None)
                if v is None:
                    props[k] = 'N/A'
                else:
                    props[k] = 'Yes' if v else 'No'

        items.append(SimpleNamespace(**props))

    columns = {
        'name': 'Name',
        'start': {
            'label': 'Start',
            'formatter_nonempty': lambda v: v.format('ddd, MMM Do'),
        },
        'end': {
            'label': 'End',
            'formatter_nonempty': lambda v: v.format('ddd, MMM Do'),
        },
        'type': 'Type',
    }
    for t, b in running_balance.items():
        for k in b.keys():
            vr = 0
            if k == 'approved':
                vr = 1
            elif k == 'requested':
                vr = 2
            elif k == 'tentative':
                vr = 3
            columns[f'{t}_{k}'] = {
                'label': f'{t} {k}',
                'verbosity': vr,
                'formatter_nonempty': lambda v: '{:1.2f}'.format(v / 8),
            }
    columns.update({
        'days': 'Days',
        'state': 'State',
        'travel': 'Travel',
        'lodging': 'Lodging',
        'registration': 'Registration',
        'roommates': 'Roommates',
    })

    print(Table(
        args,
        items,
        columns,
    ))


def parse_args():
    year = arrow.now().year
    parser = argparse.ArgumentParser(description="Manage PTO")
    parser.add_argument('-f', '--file', help="Path to file")
    parser.add_argument('-y', '--year', type=int, default=year, help="Year to work with")
    parser.add_argument('-F', '--filter', help="Additional filter on name to disambiguate years if necessary")
    parser.add_argument('-l', '--list-years', action='store_true', help="List all years")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Verbosity level, specify multiple times")
    return parser.parse_args()


def main(args):
    data = load_file(args)
    if args.list_years:
        list_years(args, data)
    else:
        year_data = load_year(args, data)
        list_pto(args, year_data)
        # for a in f.collections[0].adjustments:
        #     print(a.date, a.hours)

if __name__ == '__main__':
    sys.exit(main(parse_args()) or 0)
