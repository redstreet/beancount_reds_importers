#!/usr/bin/env python3
"""Download account statements automatically when possible, or display a reminder of how to download them.
Multi-threaded."""

from click_aliases import ClickAliasedGroup
import asyncio
import click
import configparser
import os
import tabulate
import tqdm
import beancount_reds_importers.util.needs_update as needs_update


@click.group(cls=ClickAliasedGroup)
def cli():
    """Download account statements automatically when possible, or display a reminder of how to download them.
    Multi-threaded."""
    pass


cli.add_command(needs_update.accounts_needing_updates)


def readConfigFile(configfile):
    config = configparser.ConfigParser()
    # config.optionxform = str # makes config file case sensitive
    config.read(os.path.expandvars(configfile))
    return config


def get_sites(sites, t, config):
    return [s for s in sites if config[s]['type'] == t]


@cli.command(aliases=['list'])
@click.option('-c', '--config-file', envvar='BEAN_DOWNLOAD_CONFIG', required=True,
              help='Config file. The environment variable BEAN_DOWNLOAD_CONFIG can also be used to specify this',
              type=click.Path(exists=True))
@click.option('-s', '--sort', is_flag=True, help='Sort output')
def list_institutions(config_file, sort):
    """List institutions (sites) currently configured."""
    config = readConfigFile(config_file)
    all_sites = config.sections()
    types = set([config[s]['type'] for s in all_sites])
    for t in sorted(types):
        sites = get_sites(all_sites, t, config)
        if sort:
            sites = sorted(sites)
        name = f"{t} ({len(sites)})".ljust(14)
        print(f"{name}:", end='')
        print(*sites, sep=', ')
        print()


def get_sites_and_sections(config_file):
    if config_file and os.path.exists(config_file):
        config = readConfigFile(config_file)
        all_sites = config.sections()
        types = set([config[s]['type'] for s in all_sites])
    return all_sites, types


def complete_sites(ctx, param, incomplete):
    config_file = ctx.params['config_file']
    all_sites, _ = get_sites_and_sections(config_file)
    return [s for s in all_sites if s.startswith(incomplete)]


def complete_site_types(ctx, param, incomplete):
    config_file = ctx.params['config_file']
    _, types = get_sites_and_sections(config_file)
    return [s for s in types if s.startswith(incomplete)]


@cli.command()
@click.option('-c', '--config-file', envvar='BEAN_DOWNLOAD_CONFIG', required=True, help='Config file')
@click.option('-i', '--sites', '--institutions', help="Institutions to download (comma separated); unspecified means all",
              default='', shell_complete=complete_sites)
@click.option('-t', '--site-types', '--institution-types',
              help="Download all institutions of specified types (comma separated)",
              default='', shell_complete=complete_site_types)
@click.option('--dry-run', is_flag=True, help="Do not actually download", default=False)
@click.option('--verbose', is_flag=True, help="Verbose", default=False)
def download(config_file, sites, site_types, dry_run, verbose):  # noqa: C901
    """Download statements for the specified institutions (sites)."""

    def pverbose(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    config = readConfigFile(config_file)
    if sites:
        sites = sites.split(',')
    else:
        sites = config.sections()
        if site_types:
            site_types = site_types.split(',')
            sites_lists = [get_sites(sites, site_type, config) for site_type in site_types]
            sites = [j for i in sites_lists for j in i]

    errors = []
    success = []
    numsites = len(sites)
    displays = []
    print(f"Processing {numsites} institutions.")

    async def download_site(i, site):
        tid = f'[{i+1}/{numsites} {site}]'
        pverbose(f'{tid}: Begin')
        try:
            options = config[site]
        except KeyError:
            errors.append(site)
            displays.append([site, f"Couldn't find {site} in {config_file}"])
            return

        # We support cmd and display, and type to filter
        if 'display' in options:
            displays.append([site, f"{options['display']}"])
            success.append(site)
        if 'cmd' in options:
            cmd = os.path.expandvars(options['cmd'])
            pverbose(f"{tid}: Executing: {cmd}")
            if dry_run:
                await asyncio.sleep(2)
                success.append(site)
                pverbose(f"{tid}: Success")
            else:
                # https://docs.python.org/3.8/library/asyncio-subprocess.html#asyncio.create_subprocess_exec
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()

                if proc.returncode:
                    errors.append(site)
                else:
                    success.append(site)
                    pverbose(f"{tid}: Success")

    async def perform_downloads(sites):
        tasks = [download_site(i, site) for i, site in enumerate(sites)]
        for t in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await t

    asyncio.run(perform_downloads(sites))

    if displays:
        print()
        displays = [[i + 1, *row] for i, row in enumerate(displays)]
        click.secho(tabulate.tabulate(displays,
                    headers=["#", "Institution", "Instructions"], tablefmt="plain"), fg='blue')
        print()

    s = len(sites)
    if success:
        print(f"{len(success)}/{s} sites succeeded: {', '.join(success)}")
    if errors:
        click.secho(f"{len(errors)}/{s} sites failed:    {', '.join(errors)}", fg='red')


@cli.command(aliases=['init'])
def config_template():
    """Output a template for download.cfg that you can then use to build your own."""

    path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(*[path, 'template.cfg'])) as f:
        for line in f:
            print(line, end='')


if __name__ == '__main__':
    cli()
