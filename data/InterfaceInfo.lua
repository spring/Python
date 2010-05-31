--
--  Info Definition Table format
--
--
--  These keywords must be lowercase for LuaParser to read them.
--
--  key:      user defined or one of the AI_INTERFACE_PROPERTY_* defines in
--            SAIInterfaceLibrary.h
--  value:    the value of the property
--  desc:     the description (could be used as a tooltip)
--
--
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

local infos = {
	{
		key    = 'shortName',
		value  = 'Python',
		desc   = 'machine conform name.',
	},
	{
		key    = 'version',
		value  = '0.1',
	},
	{
		key    = 'name',
		value  = 'default Python AI Interface',
		desc   = 'human readable name.',
	},
	{
		key    = 'description',
		value  = 'This interface is needed for Python AIs',
		desc   = 'tooltip.',
	},
	{
		key    = 'url',
		value  = 'http://springrts.com/wiki/AIWrapper:PyAI',
		desc   = 'URL with more detailed info about the AI',
	},
	{
		key    = 'supportedLanguages',
		value  = 'Python',
	},
}

return infos
