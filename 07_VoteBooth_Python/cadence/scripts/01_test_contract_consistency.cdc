/**
    Script to test the contract consistency of all contracts in this project, namely:
    1. BallotStandard.cdc
    2. ElectionStandard.cdc
    3. VoteBoxStandard.cdc
    4. VoteBooth

    The logic is to check that each contract in that list apart from #1 was deployed into the same account.
    If the project is found consistent, this script returns the address of the account where all the project contracts are deployed into.

    @returns Address? If the project is found consistent, this script returns the address of the account where all the project contracts were deployed into. Otherwise, if an inconsistency is found, the script returns nil.
**/
import BallotStandard from 0x287f5c8b0865c516
import ElectionStandard from 0x287f5c8b0865c516
import VoteBoxStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

access(all) fun main(): Address? {
    let ballotDeployer: Address = BallotStandard.deployerAddress
    let electionDeployer: Address = ElectionStandard.deployerAddress
    let voteBoxDeployer: Address = VoteBoxStandard.deployerAddress
    let voteboothDeployer: Address = VoteBooth.deployerAddress

    if (electionDeployer == ballotDeployer) {
        if (VoteBooth.verbose) {
            log(
                "Election standard is consistent."
            )
        }
    }
    else {
        if (VoteBooth.verbose) {
            log(
            "WARNING: BallotStandard(`ballotDeployer.toString()`) and ElectionStandard(`electionDeployer.toString()`) are deployed into different accounts!"
            )
        }

        return nil
    }

    if (voteBoxDeployer == electionDeployer) {
        if (VoteBooth.verbose) {
            log(
                "VoteBox standard is consistent."
            )
        }
    }
    else {
        if (VoteBooth.verbose) {
            log(
            "WARNING: VoteBoxStandard(`voteBoxDeployer.toString()`) and ElectionStandard(`electionDeployer.toString()`) are deployed into different accounts!"
            )
        }

        return nil
    }

    if (voteboothDeployer == voteBoxDeployer) {
        if (VoteBooth.verbose) {
            log(
            "VoteBooth and the remaining standards are consistently deployed at `voteboothDeployer.toString()`"
            )
        }
    }
    else {
        if (VoteBooth.verbose) {
            log(
            "WARNING: VoteBooth(`voteboothDeployer.toString()`) and VoteBoxStandard(`voteBoxDeployer.toString()`) are deployed into different accounts!"
            )
        }

        return nil
    }

    return voteboothDeployer
}