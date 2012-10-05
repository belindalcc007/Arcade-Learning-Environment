/* *****************************************************************************
 * A.L.E (Arcade Learning Environment)
 * Copyright (c) 2009-2012 by Yavar Naddaf, Joel Veness, Marc G. Bellemare and 
 *   the Reinforcement Learning and Artificial Intelligence Laboratory
 * Released under the GNU General Public License; see License.txt for details. 
 *
 * Based on: Stella  --  "An Atari 2600 VCS Emulator"
 * Copyright (c) 1995-2007 by Bradford W. Mott and the Stella team
 *
 * *****************************************************************************
 */
#ifndef __JOURNEYESCAPE_HPP__
#define __JOURNEYESCAPE_HPP__

#include "../RomSettings.hpp"


/* RL wrapper for Journey Escape */
class JourneyEscapeSettings : public RomSettings {

    public:

        JourneyEscapeSettings();

        // reset
        void reset();

        // is end of game
        bool isTerminal() const;

        // get the most recently observed reward
        reward_t getReward() const;

        // the rom-name
        const char* rom() const { return "journey_escape"; }

        // create a new instance of the rom
        RomSettings* clone() const;

        // is an action legal
        bool isLegal(const Action& a) const;

        // process the latest information from ALE
        void step(const System& system);

        // saves the state of the rom settings
        void saveState(Serializer & ser);
    
        // loads the state of the rom settings
        void loadState(Deserializer & ser);

        // Journey Escape requires the fire action to start the game
        ActionVect getStartingActions();

    private:

        bool m_terminal;
        reward_t m_reward;
        reward_t m_score;
};

#endif // __JOURNEYESCAPE_HPP__
