import time
from urllib.parse import urlencode
import re

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

from apps.article.models import Article
from .models import Taxon, Occurrence, Dataset, RawDataOccurrence, DatasetOrganization
from .helpers.species import get_species_info

def search_all(request):
    if request.method == 'POST':
        q = request.POST.get('q', '')
        url = '/search/'
        if q:
            url = '{}?q={}'.format(url, q)
        return HttpResponseRedirect(url)
    elif request.method == 'GET':
        q = request.GET.get('q', '')
        ## 預設最多每組 20 筆
        count = 0
        article_rows = []
        for x in Article.objects.filter(title__icontains=q).all()[:20]:
            article_rows.append({
                'title': x.title,
                'content': x.content,
                'url': x.get_absolute_url()
            })
        count += len(article_rows)

        occur_rows = []
        for x in RawDataOccurrence.objects.values('vernacularname', 'scientificname', 'taibif_id', 'taibif_dataset_name').filter(Q(scientificname__icontains=q)|Q(vernacularname__icontains=q)).all()[:20]:
            occur_rows.append({
                'title': '{} {}'.format(x['scientificname'], x['vernacularname']),
                'content': '資料集: {}'.format(x['taibif_dataset_name']),
                'url': '/occurrence/{}'.format(x['taibif_id']) #x.get_absolute_url()
            })
        count += len(occur_rows)

        dataset_rows = []
        for x in Dataset.objects.values('title', 'description', 'name').filter(Q(title__icontains=q) | Q(description__icontains=q)).exclude(status='Private').all()[:20]:
            dataset_rows.append({
                'title': x['title'],
                'content':x['description'],
                'url': '/dataset/{}'.format(x['name'])
            })
        count += len(dataset_rows)

        species_rows = []
        for x in Taxon.objects.filter(Q(name__icontains=q) | Q(name_zh__icontains=q)).all():
            species_rows.append({
                'title': '[{}] {}'.format(x.get_rank_display(), x.get_name()),
                'content': '物種數: {}'.format(x.count),
                'url': '/species/{}'.format(x.id),
            })
        count += len(species_rows)

        publisher_rows = []
        for x in DatasetOrganization.objects.filter(name__icontains=q).all():
            publisher_rows.append({
                'title': x.name,
                'content': x.description,
                'url': '/publisher/{}'.format(x.id)
            })
        count += len(publisher_rows)

        context = {
            'count': count,
            'results': [
                {
                    'cat': 'article',
                    'label': '文章',
                    'rows': article_rows
                },
                {
                    'cat': 'occurrence',
                    'label': '出現紀錄',
                    'rows': occur_rows
                },
                {
                    'cat': 'species',
                    'label': '物種',
                    'rows': species_rows
                },
                {
                    'cat': 'dataset',
                    'label': '資料集',
                    'rows': dataset_rows
                },
                {
                    'cat': 'publisher',
                    'label': '發布者',
                    'rows': publisher_rows
                },
            ]
        }
        return render(request, 'search_all.html', context)

def search_old(request):
    page = 0
    q = ''
    if request.method == 'POST':
        page = request.POST.get('page', 0)
        q = request.POST.get('q', '')
        url = request.path
        qs = {}
        if page:
            qs['page'] = page
        if q:
            qs['q'] = q

        if qs:
            url += '?' + urlencode(qs)
        return HttpResponseRedirect(url)
    else:
        page = request.GET.get('page', '')
        q = request.GET.get('q', '')

    #kingdom = request.GET.get('kingdom', '')

    result = do_search(q, page)
    result['search_tags'] = []
    for i in request.GET:
        if i != 'page':
            if i == 'q':
                result['search_tags'].append(request.GET[i])
            else:
                result['search_tags'].append('{}:{}'.format(i, request.GET[i]))
    return render(request, 'search.html', result)


def occurrence_view(request, taibif_id):
    occurrence = get_object_or_404(RawDataOccurrence, taibif_id=taibif_id)

    context = {
        'occurrence': occurrence
    }
    '''context['fields'] = RawDataOccurrence._meta.get_fields()
    context['occur'] = obj
    data = {}
    for i in RawDataOccurrence._meta.get_fields():
        if not i.is_relation:
            data[i.column] = getattr(obj, i.name, '')
    context['columns'] = data
    n = RawDataOccurrence.objects.values('scientificname','taibif_dataset_name','eventdate', 'decimallongitude', 'decimallatitude').filter(scientificname__exact=obj.scientificname).all()
    context['n'] = n
    dataset = {}
    for i in n:
        if i['taibif_dataset_name'] not in dataset:
            dataset[i['taibif_dataset_name']] = 0
        dataset[i['taibif_dataset_name']] += 1
    context['in_dataset'] = dataset'''
    return render(request, 'occurrence.html', context)

def dataset_view(request, name):
    context = {}
    context['dataset'] = get_object_or_404(Dataset, name=name)
    return render(request, 'dataset.html', context)

def publisher_view(request, pk):
    context = {}
    context['publisher'] = get_object_or_404(DatasetOrganization, pk=pk)
    return render(request, 'publisher.html', context)

def species_view(request, pk):
    context = {}
    taxon = get_object_or_404(Taxon, pk=pk)
    '''q = RawDataOccurrence.objects.values('scientificname', 'taibif_dataset_name', 'decimallatitude', 'decimallongitude')
    if taxon.rank == 'kingdom':
        q = q.filter(Q(kingdom=taxon.name)|Q(kingdom=taxon.name_zh))
    elif taxon.rank == 'phylum':
        q = q.filter(Q(phylum=taxon.name)|Q(phylum=taxon.name_zh))
    elif taxon.rank == 'class':
        q = q.filter(Q(class_field=taxon.name)|Q(class_field=taxon.name_zh))
    elif taxon.rank == 'order':
        q = q.filter(Q(order=taxon.name)|Q(order=taxon.name_zh))
    elif taxon.rank == 'family':
        q = q.filter(Q(family=taxon.name)|Q(family=taxon.name_zh))
    elif taxon.rank == 'genus':
        q = q.filter(Q(genus=taxon.name)|Q(genus=taxon.name_zh))
    elif taxon.rank == 'species':
        q = q.filter(Q(scientificname__icontains=taxon.name)|Q(scientificname__icontains=taxon.name_zh))'''
    q = RawDataOccurrence.objects.values('taibif_dataset_name', 'decimallatitude', 'decimallongitude').filter(scientificname=taxon.name).all()
    #q.count()
    occurrence_list = []
    rows = None
    lat = 0
    lng = 0
    if taxon.rank == 'species':
        sp_info = get_species_info(taxon)
        # HACK species 先全抓, 高層的資料多, 效能差
        rows = q.all()
    else:
        rows = q.all()[:20]

    for r in rows:
        if r['decimallatitude'] and r['decimallongitude']:
            lat += float(r['decimallatitude'])
            lng += float(r['decimallongitude'])
            occurrence_list.append({
                'taibif_dataset_name': r['taibif_dataset_name'],
                'decimallatitude': float(r['decimallatitude']),
                'decimallongitude': float(r['decimallongitude']),
            })

    #dataset_list = q.annotate(dataset=Count('id')).all()
    n = len(occurrence_list)

    context = {
        'taxon': taxon,
        'occurrence_list': occurrence_list,
        #'dataset_list': dataset_list
    }
    if taxon.rank == 'species':
        context['species_info'] = sp_info

    if n:
        context['map_view'] = [lat/n, lng/n]
    #n =
    return render(request, 'species.html', context)

def search_view(request):
    context = {'env': settings.ENV}
    return render(request, 'search.html', context)
