/*
 * from the ai headerfile 
 */
#if !defined BUILDING_SKIRMISH_AI
#       error BUILDING_SKIRMISH_AI should be defined when building Skirmish AIs
#endif
#if !defined BUILDING_AI
#       error BUILDING_AI should be defined when building Skirmish AIs
#endif
#if defined BUILDING_AI_INTERFACE
#       error BUILDING_AI_INTERFACE should not be defined when building Skirmish AIs
#endif
#if defined SYNCIFY
#       error SYNCIFY should not be defined when building Skirmish AIs
#endif




// for a list of the functions that have to be exported,
// see struct SSkirmishAILibrary in "ExternalAI/Interface/SSkirmishAILibrary.h"

// static AI library methods (optional to implement)
//EXPORT(enum LevelOfSupport) getLevelOfSupportFor(int teamId,
//              const char* engineVersionString, int engineVersionNumber,
//              const char* aiInterfaceShortName, const char* aiInterfaceVersion);

EXPORT(int) init(int teamId,
                unsigned int infoSize,
                const char** infoKeys, const char** infoValues,
                unsigned int optionsSize,
                const char** optionsKeys, const char** optionsValues);

EXPORT(int) release(int teamId);

EXPORT(int) handleEvent(int teamId, int topic, const void* data);

/*
 * end ai headerfile
 */

#include <Python.h>
#include "ExternalAI/Interface/aidefines.h"
#include "ExternalAI/Interface/ELevelOfSupport.h"
#include "ExternalAI/Interface/AISCommands.h"
#include "ExternalAI/Interface/AISEvents.h"
