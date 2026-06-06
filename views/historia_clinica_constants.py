THEME = {
    'primary': 'blue-600',
    'primary_dark': 'blue-800',
    'secondary': 'slate-500',
    'accent': 'indigo-600',
    'success': 'green-900',
    'error': 'red-500',
    'warning': 'deep-orange',
    'bg_light': 'bg-slate-50',
    'surface': 'bg-white'
}

CARD_CLASSES = 'w-full shadow-xl rounded-2xl border border-blue-100 bg-white'
HC_CARD_PROFESSIONAL = f'w-full p-4 shadow-sm rounded-xl  {THEME["surface"]} hover:shadow-md transition-all duration-300'
HC_SECTION_CARD = 'w-full mb-3 p-4  border border-slate-100 shadow-none'
INPUT_CLASSES = ' text-xs rounded-lg focus:border-blue-500'
HEADER_TITLE_CLASSES = f'text-xl font-bold text-slate-800 border-l-4 border-{THEME["primary"]} pl-3'

BASE_BUTTON_CLASSES = ' font-medium rounded-lg py-2 transition-all shadow-md hover:shadow-lg'
PRIMARY_BUTTON_CLASSES = f'bg-blue-500 hover:bg-blue-700 text-white {BASE_BUTTON_CLASSES}'
SUCCESS_BUTTON_CLASSES = f'bg-green-800 hover:bg-green-600 text-white {BASE_BUTTON_CLASSES}'
DANGER_BUTTON_CLASSES = 'bg-red-500 hover:bg-red-700 text-white font-semibold rounded-full p-2 shadow transition-all'
HEADER_NAV_BUTTON_CLASSES = 'text-white hover:bg-blue-700/50 transition-all rounded-full p-2'
HC_ICON_ACTION_BUTTON = 'text-gray-600 hover:text-indigo-600 transition-colors duration-200 rounded-full p-2'
