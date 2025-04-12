import sys
import argparse
import functools

from tabulate import tabulate
import arrow
from colorist import Color, Effect

from lib import storage, data


class ACTUALLY_NONE:
    pass


def _arg_date(val):
    return arrow.get(val).replace(hour=0, minute=0, second=0, microsecond=0)


def _arg_maybe_bool(val):
    val = str(val).strip().lower()
    return val and val[0] in ['t', 'y', '1']

def _arg_maybe_bool_or_none(val):
    val = str(val).strip().lower()
    if val[0] in ['-', 'x']:
        return ACTUALLY_NONE
    return _arg_maybe_bool(val)


def _arg_duration(val):
    if val:
        val = str(val)
        mul = 1.0
        if val.endswith('d'):
            mul = 8.0
            val = val[:-1]
        val = float(val) * mul
    return val


def _has_collection(callback):
    @functools.wraps(callback)
    def _has_collection_wrap(args, *a, **ka):
        colls = storage.load()
        if args.collection:
            by_fname = {o.filename: o for o in colls}
            coll = by_fname[args.collection]
        else:
            coll = colls[-1]
        return callback(args, coll, *a, **ka)
    return _has_collection_wrap


def _has_type(arg, optional=False):
    def _has_type_impl(callback):
        @functools.wraps(callback)
        def _has_type_wrap(args, coll, *a, **ka):
            by_key = {t.key: t for t in coll.pto_types}
            if optional:
                type_ = by_key.get(getattr(args, arg))
            else:
                type_ = by_key[getattr(args, arg)]
            return callback(args, coll, type_, *a, **ka)
        return _has_type_wrap
    return _has_type_impl


def _has_entry(arg, optional=False):
    def _has_entry_impl(callback):
        @functools.wraps(callback)
        def _has_entry_wrap(args, coll, *a, **ka):
            entry = coll.entries[getattr(args, arg) - 1]
            return callback(args, coll, entry, *a, **ka)
        return _has_entry_wrap
    return _has_entry_impl


def cmd_list_files(args):
    rows = [[c.filename, c.start.format('YYYY-MM-DD')] for c in storage.load()]
    print(tabulate(rows, headers=['Filename', 'Starts']))


def cmd_new_file(args):
    coll = data.PTOCollection(start=args.start)
    storage.save(coll)
    print(f"Saved new PTO collection to {coll.filename}")


@_has_collection
def cmd_add_type(args, coll):
    kw = dict(
        key=args.key,
        name=args.name,
        short=args.short_name,
        order=args.order,
        init_balance=args.balance,
        resolution=args.resolution,
        accrued=args.accrued,
    )
    if args.accrued:
        if args.accrual_days is not None:
            kw['accrual_days'] = args.accrual_days
        if args.accrual_amount is not None:
            kw['accrual_amount'] = args.accrual_amount
        if args.accrual_total is not None:
            kw['accrual_total'] = args.accrual_total
    type_ = data.PTOType(**kw)
    coll.pto_types.append(type_)
    storage.save(coll)
    print(f"Added new PTO type {type_.name} ({type_.key}) to collection {coll.filename}")


@_has_collection
@_has_type('key')
def cmd_edit_type(args, coll, type_):
    if args.name is not None:
        type_.name = args.name

    if args.short_name is not None:
        type_.short = args.short_name

    if args.name is not None:
        type_.name = args.name

    if args.order is not None:
        type_.order = args.order

    if args.balance is not None:
        type_.init_balance = args.balance

    if args.resolution is not None:
        type_.resolution = args.resolution

    if args.accrued is not None:
        type_.accrued = args.accrued

    if args.accrual_days is not None:
        type_.accrual_days = args.accrual_days

    if args.accrual_amount is not None:
        type_.accrual_amount = args.accrual_amount

    if args.accrual_total is not None:
        type_.accrual_total = args.accrual_total

    storage.save(coll)
    print(f"Saved PTO type {type_.name} ({type_.key}) to collection {coll.filename}")


@_has_collection
@_has_type('type')
def cmd_add_entry(args, coll, type_):
    end = None
    if args.end:
        end = args.end
    elif args.duration:
        end = args.date.shift(hours=int(args.duration * 24.0))
    kw = dict(
        name=args.name,
        pto_type=type_.key,
        date=args.date,
        amount=args.amount,
        end=end,
        tentative=args.tentative,
        requested=args.requested,
        approved=args.approved,
        travel=args.travel,
        lodging=args.lodging,
        registration=args.registration,
        roommates=args.roommates,
    )
    ent = data.PTOEntry(**kw)
    coll.entries.append(ent)
    storage.save(coll)
    print(f"Added entry {ent.name} ({type_.name}) to collection {coll.filename}")


@_has_collection
@_has_type('type', optional=True)
@_has_entry('id')
def cmd_edit_entry(args, coll, entry, type_):
    if type_ is not None:
        entry.pto_type = type_.key

    if args.name is not None:
        entry.name = args.name

    if args.date is not None:
        entry.date = args.date

    if args.amount is not None:
        entry.amount = args.amount

    end = None
    if args.end:
        end = args.end
    elif args.duration:
        end = entry.date.shift(hours=int(args.duration * 24.0))

    if end is not None:
        entry.end = end

    if args.tentative is not None:
        entry.tentative = args.tentative

    if args.requested is not None:
        entry.requested = args.requested

    if args.approved is not None:
        entry.approved = args.approved

    if args.travel is not ACTUALLY_NONE:
        entry.travel = args.travel

    if args.lodging is not ACTUALLY_NONE:
        entry.lodging = args.lodging

    if args.registration is not ACTUALLY_NONE:
        entry.registration = args.registration

    if args.roommates is not ACTUALLY_NONE:
        entry.roommates = args.roommates

    storage.save(coll)
    print(f"Updated entry {entry.name} in collection {coll.filename}")


@_has_collection
def cmd_list_entries(args, coll):
    entries = [(True, m.model_copy()) for m in coll.entries]
    types = {m.key: m for m in coll.pto_types}
    bal_tentative = {m.key: 0.0 for m in coll.pto_types}
    bal_planned = {m.key: 0.0 for m in coll.pto_types}
    bal_requested = {m.key: 0.0 for m in coll.pto_types}
    bal_approved = {m.key: 0.0 for m in coll.pto_types}
    for t in coll.pto_types:
        if t.init_balance:
            entries.append((False, data.PTOEntry(
                name='Initial Balance',
                pto_type=t.key,
                date=coll.start.shift(days=-1),
                amount=t.init_balance,
            )))
        if t.accrued:
            # add an accrual entry per accrual day as well as one for any initial balance
            for m in range(1, 13):
                for d in t.accrual_days:
                    try:
                        ts = coll.start.replace(month=m, day=d)
                    except ValueError:
                        # day out of range; use last day
                        ts = coll.start
                        if m == 12:
                            ts = ts.shift(years=1).replace(month=1, day=1).shift(days=-1)
                        else:
                            ts = ts.replace(month=m + 1, day=1).shift(days=-1)
                    entries.append((False, data.PTOEntry(
                        name='Accrual',
                        pto_type=t.key,
                        date=ts,
                        amount=t.accrual_amount or t.accrual_total / (12 * len(t.accrual_days)),
                    )))
    entries = list(sorted(entries, key=lambda e: e[1].date))
    headers = ['ID', 'Name', 'Date', 'Status']
    for pto_type in types.values():
        for h in ('Tentative', 'Planned', 'Requested', 'Approved'):
            headers.append(h + ' - ' + pto_type.short_name)
    headers += ['Travel?', 'Lodging?', 'Registration?', 'Roommates?']
    # TODO: make this optional
    header_short_map = {
        'Tentative': 'Tn',
        'Planned': 'Pl',
        'Requested': 'Rq',
        'Approved': 'Ap',
        'Travel': 'Tr',
        'Lodging': 'Lo',
        'Registration': 'Re',
        'Roommates': 'Rm',
    }
    for i, v in enumerate(list(headers)):
        for k, e in header_short_map.items():
            if k in v:
                v = v.replace(k, e)
                headers[i] = v

    rows = []
    def f_maybe_bool(value):
        if value is None:
            return Effect.DIM + Color.WHITE + 'NA' + Color.OFF + Effect.DIM_OFF
        elif value:
            return Color.GREEN + 'Y' + Color.OFF
        return Color.RED + 'N' + Color.OFF

    def f_days(hours):
        return '{:1.2f}'.format(hours / 8.0)

    def f_color_num(n, tgood=3, tok=1):
        if float(n) >= tgood:
            return Color.GREEN + n + Color.OFF
        elif float(n) >= tok:
            return Color.YELLOW + n + Color.OFF
        return Color.RED + n + Color.OFF

    def f_status(entry):
        if entry.approved:
            return Color.GREEN + 'Approved' + Color.OFF
        elif entry.requested:
            return Color.YELLOW + 'Requested' + Color.OFF
        elif entry.tentative:
            return Effect.DIM + Color.WHITE + 'Tentative' + Color.OFF + Effect.DIM_OFF
        else:
            return Color.RED + 'Planned' + Color.OFF

    def f_for_status(entry, text):
        if entry.tentative:
            return Effect.DIM + Color.WHITE + text + Color.OFF + Effect.DIM_OFF
        elif entry.approved and all((v is None or v is True for v in (entry.travel, entry.lodging, entry.registration, entry.roommates))):
            return Color.GREEN + text + Color.OFF
        return Color.RED + text + Color.OFF

    for is_pto, entry in entries:
        if is_pto:
            if entry.approved:
                bal_approved[entry.pto_type] -= entry.amount
                bal_requested[entry.pto_type] -= entry.amount
                bal_planned[entry.pto_type] -= entry.amount
                bal_tentative[entry.pto_type] -= entry.amount
            elif entry.requested:
                bal_requested[entry.pto_type] -= entry.amount
                bal_planned[entry.pto_type] -= entry.amount
                bal_tentative[entry.pto_type] -= entry.amount
            elif entry.tentative:
                bal_tentative[entry.pto_type] -= entry.amount
            else:
                bal_planned[entry.pto_type] -= entry.amount
                bal_tentative[entry.pto_type] -= entry.amount
            row = [
                entry._id,
                f_for_status(entry, entry.name),
                entry.date.format('YYYY-MM-DD'),
                f_status(entry),
            ]
            for pto_type in types.values():
                if pto_type.key == entry.pto_type:
                    row += [
                        f_color_num(f_days(bal_tentative[entry.pto_type])),
                        f_color_num(f_days(bal_planned[entry.pto_type])),
                        f_color_num(f_days(bal_requested[entry.pto_type])),
                        f_color_num(f_days(bal_approved[entry.pto_type])),
                    ]
                else:
                    row += ['', '', '', '']
            row += [
                f_maybe_bool(entry.travel),
                f_maybe_bool(entry.lodging),
                f_maybe_bool(entry.registration),
                f_maybe_bool(entry.roommates),
            ]
            rows.append(row)
        else:
            bal_approved[entry.pto_type] += entry.amount
            bal_requested[entry.pto_type] += entry.amount
            bal_planned[entry.pto_type] += entry.amount
            bal_tentative[entry.pto_type] += entry.amount
            row = [
                '',
                Effect.DIM + Color.WHITE + types[entry.pto_type].short_name + Color.OFF + Effect.DIM_OFF,
                entry.date.format('YYYY-MM-DD'),
                Effect.DIM + Color.WHITE + '+' + Color.OFF + Effect.DIM_OFF,
            ]
            for pto_type in types.values():
                if pto_type.key == entry.pto_type:
                    row += [
                        f_color_num(f_days(bal_tentative[entry.pto_type])),
                        f_color_num(f_days(bal_planned[entry.pto_type])),
                        f_color_num(f_days(bal_requested[entry.pto_type])),
                        f_color_num(f_days(bal_approved[entry.pto_type])),
                    ]
                else:
                    row += ['', '', '', '']
            row += [
                '',
                '',
                '',
                '',
            ]
            rows.append(row)
    print(tabulate(rows, headers=headers))

# class PTOEntry(BaseModel):
#     class Config:
#         arbitrary_types_allowed = True

#     name: str
#     pto_type: str
#     date: arrow.arrow.Arrow
#     amount: float
#     end: Optional[arrow.arrow.Arrow] = None
#     tentative: bool = False
#     requested: bool = False
#     approved: bool = False
#     travel: Optional[bool] = None
#     lodging: Optional[bool] = None
#     registration: Optional[bool] = None
#     roommates: Optional[bool] = None


def parse_args():
    parser = argparse.ArgumentParser(description="Manage PTO")
    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND', help="Subcommand")

    files_parser = subparsers.add_parser('files', aliases=['coll', 'collections'], help="List available files/collections")
    files_parser.set_defaults(callback=cmd_list_files)

    new_parser = subparsers.add_parser('new', help="Create a new PTO collection")
    new_parser.add_argument('-s', '--start',
        type=_arg_date,
        default=arrow.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
        help="Start date, defaults to first of the year",
    )
    new_parser.set_defaults(callback=cmd_new_file)

    type_parser = subparsers.add_parser('type', help="Create or edit a PTO type")
    type_parser.add_argument('-c', '--collection', help="Collection to edit, defaults to latest")
    type_subparsers = type_parser.add_subparsers(metavar='TYPE_COMMAND', help="Type subcommand")

    type_add_parser = type_subparsers.add_parser('add', help="Add a new PTO type")
    type_add_parser.add_argument('key', help="Type key for reference")
    type_add_parser.add_argument('name', help="Type name")
    type_add_parser.add_argument('-s', '--short-name', help="Type short name")
    type_add_parser.add_argument('-o', '--order', type=int, default=0, help="Order of this type; determines which PTO is used first in some situations")
    type_add_parser.add_argument('-b', '--balance', type=_arg_duration, default=0, help="Initial balance for this type")
    type_add_parser.add_argument('-r', '--resolution', type=float, default=1, help="Multiple of hours that may be used at once")
    type_add_parser.add_argument('-A', '--not-accrued', action='store_false', dest='accrued', help="This type of PTO is available immediately and is not accrued")
    type_add_parser.add_argument('-d', '--accrual-days', action='append', type=int, help="Days of the month on which this PTO is accrued, if applicable.  May be specified more than once")
    type_add_parser.add_argument('-a', '--accrual-amount', type=float, help="Amount of PTO accrued on each of the accrual days")
    type_add_parser.add_argument('-t', '--accrual-total', type=float, help="Amount of PTO accrued over the course of a year (amount per accrual day is calculated from this)")
    type_add_parser.set_defaults(callback=cmd_add_type)

    type_edit_parser = type_subparsers.add_parser('edit', help="Add a new PTO type")
    type_edit_parser.add_argument('key', help="Type key to edit")
    type_edit_parser.add_argument('-n', '--name', help="Type name")
    type_edit_parser.add_argument('-s', '--short-name', help="Type short name")
    type_edit_parser.add_argument('-o', '--order', type=int, help="Order of this type; determines which PTO is used first in some situations")
    type_edit_parser.add_argument('-b', '--balance', type=_arg_duration, help="Initial balance for this type")
    type_edit_parser.add_argument('-r', '--resolution', type=_arg_duration, help="Multiple of hours that may be used at once")
    type_edit_parser.add_argument('-A', '--accrued', type=_arg_maybe_bool, help="If true (yes/true/1), this type of PTO is available immediately and is not accrued, otherwise it is accrued")
    type_edit_parser.add_argument('-d', '--accrual-days', action='append', type=int, help="Days of the month on which this PTO is accrued, if applicable.  May be specified more than once")
    type_edit_parser.add_argument('-a', '--accrual-amount', type=_arg_duration, help="Amount of PTO accrued on each of the accrual days")
    type_edit_parser.add_argument('-t', '--accrual-total', type=_arg_duration, help="Amount of PTO accrued over the course of a year (amount per accrual day is calculated from this)")
    type_edit_parser.set_defaults(callback=cmd_edit_type)

    entry_parser = subparsers.add_parser('entry', aliases=['e'], help="Create or edit a PTO entry")
    entry_parser.add_argument('-c', '--collection', help="Collection to add to, defaults to latest")
    entry_subparsers = entry_parser.add_subparsers(metavar='TYPE_COMMAND', help="Type subcommand")

    entry_add_parser = entry_subparsers.add_parser('add', help="Add a new PTO entry")
    entry_add_parser.add_argument('type', help="PTO type to add")
    entry_add_parser.add_argument('name', help="Name of this entry")
    entry_add_parser.add_argument('date', type=_arg_date, help="Date on which this entry starts")
    entry_add_parser.add_argument('amount', type=_arg_duration, help="Amount of PTO needed")
    entry_add_parser.add_argument('-e', '--end', type=_arg_date, help="End date of entry")
    entry_add_parser.add_argument('-d', '--duration', type=float, help="If given, number of days from start that end is calculated")
    entry_add_parser.add_argument('-t', '--tentative', action='store_true', help="This entry is tenative (not included in final balance; a separate calculation is done)")
    entry_add_parser.add_argument('-r', '--requested', action='store_true', help="Time off has been requested for this entry")
    entry_add_parser.add_argument('-a', '--approved', action='store_true', help="Time off has been approved for this entry")
    entry_add_parser.add_argument('-T', '--travel', type=_arg_maybe_bool, help="Travel has or has not been arranged")
    entry_add_parser.add_argument('-l', '--lodging', type=_arg_maybe_bool, help="Lodging has or has not been arranged")
    entry_add_parser.add_argument('-R', '--registration', type=_arg_maybe_bool, help="Registration has or has not been purchased")
    entry_add_parser.add_argument('-m', '--roommates', type=_arg_maybe_bool, help="Roommates have or have not been secured")
    entry_add_parser.set_defaults(callback=cmd_add_entry)

    entry_edit_parser = entry_subparsers.add_parser('edit', help="Edit an existing PTO entry")
    entry_edit_parser.add_argument('id', type=int, help="ID of the entry to edit")
    entry_edit_parser.add_argument('-y', '--type', help="PTO type to use")
    entry_edit_parser.add_argument('-n', '--name', help="Name of this entry")
    entry_edit_parser.add_argument('-D', '--date', type=_arg_date, help="Date on which this entry starts")
    entry_edit_parser.add_argument('-A', '--amount', type=_arg_duration, help="Amount of PTO needed")
    entry_edit_parser.add_argument('-e', '--end', type=_arg_date, help="End date of entry")
    entry_edit_parser.add_argument('-d', '--duration', type=float, help="If given, number of days from start that end is calculated")
    entry_edit_parser.add_argument('-t', '--tentative', type=_arg_maybe_bool, help="This entry is tenative (not included in final balance; a separate calculation is done)")
    entry_edit_parser.add_argument('-r', '--requested', type=_arg_maybe_bool, help="Time off has been requested for this entry")
    entry_edit_parser.add_argument('-a', '--approved', type=_arg_maybe_bool, help="Time off has been approved for this entry")
    entry_edit_parser.add_argument('-T', '--travel', type=_arg_maybe_bool_or_none, help="Travel has or has not been arranged")
    entry_edit_parser.add_argument('-l', '--lodging', type=_arg_maybe_bool_or_none, help="Lodging has or has not been arranged")
    entry_edit_parser.add_argument('-R', '--registration', type=_arg_maybe_bool_or_none, help="Registration has or has not been purchased")
    entry_edit_parser.add_argument('-m', '--roommates', type=_arg_maybe_bool_or_none, help="Roommates have or have not been secured")
    entry_edit_parser.set_defaults(callback=cmd_edit_entry)

    entry_list_parser = entry_subparsers.add_parser('list', aliases=['ls'], help="List PTO entries")
    entry_list_parser.set_defaults(callback=cmd_list_entries)

    return parser.parse_args()


def main(args):
    try:
        cb = args.callback
    except AttributeError:
        # TODO: cb=default if not command
        pass

    return cb(args)


if __name__ == '__main__':
    sys.exit(main(parse_args()) or 0)
